.mode csv
.separator ";"
.header off
.output "federated_data/policies/qtable.csv"

/* ---------------------------------- Input Parameters ---------------------------------- */

drop table if exists input; -- input (and algorithm constants)
create table input (learning_rate float, episodes int, tries int, discount float, penalty float, epsilon float);

drop table if exists rewards; -- rewards
create table rewards (i int, j int, x_ij float);
create index idx_rewards on rewards (i, j);

drop table if exists qtable; -- qtable 
create table qtable (i int, j int, k int, x_ijk float);
create index idx_qtable on qtable (i, j, k);

drop table if exists agent;
create table agent (x int, y int, init_x int, init_y int);

drop table if exists goal;
create table goal (x int, y int);

--drop table if exists rand_values;
--create table rand_values (i int, j int, uniform float, randint int);
--create index idx_rand_values on rand_values (i, j);

-- Populate tables
.import data/inputs.csv input
.import data/goal.csv goal
.import data/agent.csv agent
.import data/rewards.csv rewards
.import results/qtable-sql.csv qtable
--.import results/rnd_values.csv rand_values

/* ---------------------------- Tuple and View Initialization ---------------------------- */

-- Tuple containing the counter for episodes and tries per episode
drop table if exists counter;
create table counter (e_step int, t_step int);

-- Tuple containing the number of episode and try for that episode
drop table if exists iterations;
create table iterations (e_step int, t_step int);

-- https://www.sqlitetutorial.net/sqlite-functions/sqlite-random/
drop view if exists get_random;
create view get_random as
  select abs(1.*random()/9223372036854775807) as rnd;

-- Returns argmax of actions for the new state
drop view if exists argmax_action;
create view argmax_action (k, x_ijk) as
  select k, x_ijk
  from qtable
  where x_ijk = (select max(x_ijk) from qtable where i=(select x from agent) and j=(select y from agent))
                 and i=(select x from agent) and j=(select y from agent) limit 1;

-- Tuple holding the selected action
drop table if exists selected_action;
create table selected_action (action int, valid int);
insert into selected_action values (null, null);

-- Tuple holding new selected state and reward for transitioning
drop table if exists new_state;
create table new_state (i int, j int, reward int);
insert into new_state values (null, null, null);

-- Scalar holding the accumulated reward for an episode
drop table if exists accumulated_reward;
create table accumulated_reward (reward float);
insert into accumulated_reward values (0);

-- Scalar holding the best reward of all episodes so far
drop table if exists best_reward;
create table best_reward (reward float);
insert into best_reward values (-99999);

-- Select action based on epsilon-decreasing strategy
drop view if exists get_action;
create view get_action (a) as
  select
    case
      when (select rnd from get_random) < (select epsilon from input) then round((select rnd from get_random)*3)
      --when (select uniform from rand_values where i=(select e_step from iterations) and j=(select t_step from iterations)) <
      --            (select epsilon from input) then
      --            (select randint from rand_values where i=(select e_step from iterations) and j=(select t_step from iterations))
      else (select k from argmax_action)
    end;

-- Check if selected action is valid
drop view if exists valid_action;
create view valid_action (a) as
  select
    case
      when (select action from selected_action)=0
        and (select y from agent)>0
        and (select x_ij from rewards where i=(select x from agent) and j=(select y from agent)-1)<>(select penalty from input) then 1
      when (select action from selected_action)=1
        and (select y from agent)<(select count(*) from rewards)-1
        and (select x_ij from rewards where i=(select x from agent) and j=(select y from agent)+1)<>(select penalty from input) then 1
      when (select action from selected_action)=2
        and (select x from agent)>0
        and (select x_ij from rewards where i=(select x from agent)-1 and j=(select y from agent))<>(select penalty from input) then 1
      when (select action from selected_action)=3
        and (select x from agent)<(select count(*) from rewards)-1
        and (select x_ij from rewards where i=(select x from agent)+1 and j=(select y from agent))<>(select penalty from input) then 1
      else 0
    end;

-- Return maximum q value of new state
drop view if exists max_future_q;
create view max_future_q (a) as
  select x_ijk
  from qtable
  where x_ijk = (select max(x_ijk) from qtable where i=(select i from new_state) and j=(select j from new_state)) limit 1;

-- Flag to indicate whether agent is on goal position
drop table if exists goal_found;
create table goal_found (found int);
insert into goal_found values (0);

-- Logs
/*drop table if exists logs;
create table logs (ep int, tr int);*/

/* ---------------------------- Main Algorithm Triggers ---------------------------- */

-- Trigger to perform step
create trigger if not exists compute_step after insert on counter
when ((select max(t_step) from counter where e_step=(select max(e_step) from counter))>0 and (select found from goal_found)=0) or
     ((select e_step from counter)=0 and (select t_step from counter)=0)
begin 
  insert into iterations values ((select max(e_step) from counter),
                                 (select max(t_step) from counter where e_step=(select max(e_step) from counter)));
  delete from counter;
end;

-- Trigger resetting the state of the maze and then perform step
create trigger if not exists state_reset after insert on counter
when (select max(t_step) from counter where e_step=(select max(e_step) from counter))=0 and (select max(e_step) from counter)>0
begin
  
  -- Compare with best reward
  update best_reward set
    reward=case 
      when (select e_step from counter)=0 then (select reward from best_reward)
      when (select reward from accumulated_reward)>(select reward from best_reward) then (select reward from accumulated_reward)
      else (select reward from best_reward) end;

  -- Reset accumulated reward on new episode
  update accumulated_reward set
    reward=0;
    
  -- Decrease epsilon value on new episode until a threshold
  update input
  set epsilon = case
    when epsilon > 0.01 and (select e_step from counter)>0 then epsilon*97/100
    else epsilon*1
    end;
    
  -- Reset agent's position on new episode
  update agent set
    x=init_x,
    y=init_y;

  -- Reinitialize flag 
  update goal_found set
    found = 0;
  
  insert into iterations values ((select max(e_step) from counter),
                                 (select max(t_step) from counter where e_step=(select max(e_step) from counter)));
  delete from counter;
  
end;

-- TODO BE careful about this one. TESTING NEEDED
create trigger if not exists safe_delete after insert on counter
when (select max(t_step) from counter where e_step=(select max(e_step) from counter))>0 and (select found from goal_found)=1
begin
  delete from counter;
end;

-- Trigger running a q-learning step
create trigger if not exists q_learning after insert on iterations
begin
  -- Find next action and check if valid
  update selected_action
  set action = (select a from get_action);
  update selected_action
  set valid = (select a from valid_action);
  
  -- Create new state
  update new_state set
    i=(select
       case
         when (select action from selected_action)=2 and (select valid from selected_action)=1 then (select x from agent)-1
         when (select action from selected_action)=3 and (select valid from selected_action)=1 then (select x from agent)+1
         else (select x from agent) end),
    j=(select
       case
         when (select action from selected_action)=0 and (select valid from selected_action)=1 then (select y from agent)-1
         when (select action from selected_action)=1 and (select valid from selected_action)=1 then (select y from agent)+1
         else (select y from agent) end),
    reward=null;
  
  -- Find reward for new state
  update new_state set reward = case
    when (select i from new_state)<>(select x from agent) or (select j from new_state)<>(select y from agent) then
      (select x_ij from rewards where i=(select i from new_state) and j=(select j from new_state))
    else (select penalty from input)
    end;
    
  -- Increment the accumulated reward with new reward gained
  update accumulated_reward set reward = (select reward from accumulated_reward)+(select reward from new_state);
  
  -- Update Q value
  update qtable set x_ijk =
    -- old value
    (select x_ijk from qtable where i=(select x from agent) and j=(select y from agent) and k=(select action from selected_action))+
    (select learning_rate from input)*
    -- temporal difference
    ((select reward from new_state)+
    (select discount from input)*
    (select a from max_future_q)-
    (select x_ijk from qtable where i=(select x from agent) and j=(select y from agent) and k=(select action from selected_action)))
  where i=(select x from agent) and j=(select y from agent) and k=(select action from selected_action);

  -- Flag check whether goal was found; this works as a flag to stop this trigger
  update goal_found set
    found = case
      when (select i from new_state)=(select x from goal) and (select j from new_state)=(select y from goal) then 1
      else 0
    end;
          
  -- Logs to compare iteration results
/* insert into logs values ((select e_step from iterations), (select t_step from iterations)); */

  -- Move agent to new state
  update agent set
    x = (select i from new_state),
    y = (select j from new_state);
   
  -- Avoid having large table
  delete from iterations;
    
end;

/* ---------------------------------- Iterations ---------------------------------- */

with recursive
  episodes(e_step) as (
    values(0)
    union all
    select e_step+1 from episodes
    where e_step < (select episodes from input)-1
  ),
  tries(t_step) as (
    values(0)
    union all
    select t_step+1 from tries
    where t_step < (select tries from input)-1
  )
insert into counter select episodes.e_step, tries.t_step from episodes, tries; -- Cartesian product 

-- Compare with best reward
update best_reward set
  reward=case 
    when (select reward from accumulated_reward)>(select reward from best_reward) then (select reward from accumulated_reward)
    else (select reward from best_reward) end;

/* --------------------------------- Exporting --------------------------------- */

select * from qtable; -- Compare learned policy

.once "federated_data/rewards/best_reward.csv"
select reward from best_reward;
--select count(*), best_reward.reward as best_reward from logs, best_reward; -- Compare iteration results
