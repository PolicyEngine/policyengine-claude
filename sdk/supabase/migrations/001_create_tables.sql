-- Dashboard Builder SDK: Telemetry Tables
-- Apply via Supabase dashboard SQL editor or `supabase db push`

-- dashboard_runs: one row per workflow execution
create table if not exists public.dashboard_runs (
  id                      uuid primary key default gen_random_uuid(),
  dashboard_name          text not null,
  description             text not null,
  status                  text not null default 'running'
                            check (status in ('running', 'completed', 'failed', 'aborted')),
  started_at              timestamptz not null default now(),
  completed_at            timestamptz,
  total_duration_ms       bigint,
  total_cost_usd          numeric(10, 6),
  total_input_tokens      bigint default 0,
  total_output_tokens     bigint default 0,
  plan_yaml               jsonb,
  final_validation_report jsonb,
  git_branch              text,
  git_commit_sha          text,
  cwd                     text,
  created_by              text not null,
  metadata                jsonb default '{}'
);

create index if not exists idx_dashboard_runs_name on public.dashboard_runs(dashboard_name);
create index if not exists idx_dashboard_runs_status on public.dashboard_runs(status);
create index if not exists idx_dashboard_runs_started on public.dashboard_runs(started_at);
create index if not exists idx_dashboard_runs_created_by on public.dashboard_runs(created_by);

-- phase_runs: one row per agent invocation
create table if not exists public.phase_runs (
  id              uuid primary key default gen_random_uuid(),
  run_id          uuid not null references public.dashboard_runs(id) on delete cascade,
  phase_name      text not null,
  phase_order     integer not null,
  agent_name      text not null,
  model           text not null,
  status          text not null default 'running'
                    check (status in ('running', 'completed', 'failed', 'skipped')),
  started_at      timestamptz not null default now(),
  completed_at    timestamptz,
  duration_ms     bigint,
  duration_api_ms bigint,
  num_turns       integer,
  input_tokens    bigint default 0,
  output_tokens   bigint default 0,
  cost_usd        numeric(10, 6),
  session_id      text,
  iteration       integer not null default 1,
  prompt_hash     text,
  error_message   text,
  metadata        jsonb default '{}'
);

create index if not exists idx_phase_runs_run on public.phase_runs(run_id);
create index if not exists idx_phase_runs_phase on public.phase_runs(phase_name);
create index if not exists idx_phase_runs_model on public.phase_runs(model);

-- quality_gates: one row per gate check
create table if not exists public.quality_gates (
  id           uuid primary key default gen_random_uuid(),
  phase_run_id uuid not null references public.phase_runs(id) on delete cascade,
  run_id       uuid not null references public.dashboard_runs(id) on delete cascade,
  gate_type    text not null
                 check (gate_type in ('build', 'test', 'type_check', 'human_approval',
                                      'validation_category', 'spec_compliance')),
  gate_name    text not null,
  passed       boolean not null,
  checked_at   timestamptz not null default now(),
  duration_ms  bigint,
  details      jsonb default '{}'
);

create index if not exists idx_quality_gates_phase on public.quality_gates(phase_run_id);
create index if not exists idx_quality_gates_run on public.quality_gates(run_id);
create index if not exists idx_quality_gates_type on public.quality_gates(gate_type);

-- Row Level Security: allow publishable-key inserts and selects for multi-user shared DB
alter table public.dashboard_runs enable row level security;
alter table public.phase_runs enable row level security;
alter table public.quality_gates enable row level security;

create policy "Allow anon select on dashboard_runs" on public.dashboard_runs
  for select using (true);
create policy "Allow anon insert on dashboard_runs" on public.dashboard_runs
  for insert with check (true);
create policy "Allow anon update on dashboard_runs" on public.dashboard_runs
  for update using (true);

create policy "Allow anon select on phase_runs" on public.phase_runs
  for select using (true);
create policy "Allow anon insert on phase_runs" on public.phase_runs
  for insert with check (true);
create policy "Allow anon update on phase_runs" on public.phase_runs
  for update using (true);

create policy "Allow anon select on quality_gates" on public.quality_gates
  for select using (true);
create policy "Allow anon insert on quality_gates" on public.quality_gates
  for insert with check (true);
