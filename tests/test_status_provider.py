import importlib.util
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('provider', Path(__file__).resolve().parents[1] / 'contents/scripts/status_provider.py')
provider = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(provider)


class QuotaTests(unittest.TestCase):
    def test_codex_selects_shared_bucket_and_converts_used_to_remaining(self):
        result = {'rateLimits': {'limitId': 'other', 'primary': {'usedPercent': 99}},
                  'rateLimitsByLimitId': {'codex': {
                      'limitId': 'codex',
                      'primary': {'usedPercent': 12.3, 'windowDurationMins': 300, 'resetsAt': 2000000000},
                      'secondary': {'usedPercent': 100, 'windowDurationMins': 10080}}}}
        quota = provider.parse_codex_quota(result)
        self.assertEqual(quota['bar1_exact'], 87.7)
        self.assertEqual(quota['bar1_percent'], 88)
        self.assertEqual(quota['bar2_percent'], 0)
        self.assertEqual(quota['bar1_resets_at'], 2000000000)
        self.assertEqual(quota['bar2_label'], 'неделя')

    def test_missing_window_is_unknown_and_other_bucket_is_ignored(self):
        quota = provider.parse_codex_quota({'rateLimits': {'primary': {'usedPercent': 5, 'windowDurationMins': 60}}})
        self.assertEqual(quota['bar1_percent'], 95)
        self.assertEqual(quota['bar1_label'], '1 ч.')
        self.assertEqual(quota['bar2_percent'], -1)
        self.assertIsNone(provider.parse_codex_quota({'rateLimits': {'limitId': 'other'}}))
        self.assertIsNone(provider.parse_codex_quota({}))

    def test_agy_does_not_mix_argon_or_claude_quotas(self):
        data = {'command': {'data': {'groups': [
            {'name': 'Claude and GPT models', 'buckets': [{'window': 'weekly', 'remaining_fraction': 1}]},
            {'name': 'Gemini Models', 'buckets': [
                {'id': 'gemini-5h', 'remaining_fraction': .9945, 'reset_time': '2026-10-22T21:56:50Z'},
                {'id': 'gemini-weekly', 'remaining_fraction': .5597}]},
            {'name': 'Gemini 4 Argon', 'buckets': [{'window': 'weekly', 'remaining_fraction': .38}]}]}}}
        quota = provider.parse_agy_quota(data)
        self.assertEqual(quota['bar1_exact'], 99.5)
        self.assertEqual(quota['bar2_exact'], 56)
        self.assertGreater(quota['bar1_resets_at'], 0)
        self.assertIsNone(provider.parse_agy_quota({}))

    def test_no_invented_full_quota_for_missing_agy_fraction(self):
        quota = provider.parse_agy_quota({'command': {'data': {'groups': [
            {'name': 'Gemini Models', 'buckets': [
                {'id': 'gemini-5h'}, {'window': 'weekly', 'remaining_fraction': 0}]}]}}})
        self.assertEqual(quota['bar1_percent'], -1)
        self.assertEqual(quota['bar2_percent'], 0)

    def test_percent_clamping_and_invalid_numbers(self):
        quota = {}
        provider.set_bucket(quota, 1, -5)
        self.assertEqual(quota['bar1_percent'], 0)
        provider.set_bucket(quota, 1, 115)
        self.assertEqual(quota['bar1_percent'], 100)
        with self.assertRaises(ValueError):
            provider.set_bucket(quota, 1, float('nan'))

    def test_cache_isolation_and_failed_refresh_backoff(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'XDG_CACHE_HOME': directory + '/cache', 'XDG_STATE_HOME': directory + '/state'}):
            agy, _ = provider.cache_paths('antigravity')
            codex, _ = provider.cache_paths('codex')
            self.assertNotEqual(agy, codex)
            good = provider.unknown_quota()
            good.update(bar1_percent=42, timestamp=time.time() - 400)
            provider.write_cache(codex, good)
            with patch.object(provider, 'fetch_codex_quota', side_effect=RuntimeError('offline')) as fetch:
                provider.refresh_quota('codex')
                provider.refresh_quota('codex')
                self.assertEqual(fetch.call_count, 1)
            cached = provider.get_usage('codex')
            self.assertEqual(cached['bar1_percent'], 42)
            self.assertEqual(cached['quota_error'], 'offline')
            self.assertTrue(cached['quota_stale'])
            self.assertIsNone(provider.read_cache(agy))

    def test_reset_countdown_is_recomputed_from_absolute_time(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'XDG_CACHE_HOME': directory + '/cache', 'XDG_STATE_HOME': directory + '/state'}):
            path, _ = provider.cache_paths('codex')
            provider.write_cache(path, dict(attempted_at=time.time(), bar1_resets_at=time.time()+3665))
            self.assertEqual(provider.get_usage('codex')['bar1_reset'], '1ч 1м')

    def test_existing_cache_migrates_and_survives_cache_removal(self):
        import shutil
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {
                'XDG_CACHE_HOME': directory + '/cache', 'XDG_STATE_HOME': directory + '/state'}):
            old, _ = provider.storage_paths('antigravity', durable=False)
            snapshot = dict(bar1_percent=37, bar1_exact=36.8, bar2_percent=0, timestamp=time.time(), attempted_at=time.time())
            provider.write_cache(old, snapshot)
            with patch.object(provider, 'fetch_agy_quota') as fetch:
                provider.refresh_quota('antigravity')
                fetch.assert_not_called()
            shutil.rmtree(directory + '/cache')
            self.assertEqual(provider.get_usage('antigravity')['bar1_percent'], 37)
            self.assertEqual(provider.get_usage('antigravity')['bar2_percent'], 0)
            state, _ = provider.cache_paths('antigravity')
            self.assertTrue(Path(state).is_file())

    def test_no_saved_quota_stays_unknown_on_network_failure(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {
                'XDG_CACHE_HOME': directory + '/cache', 'XDG_STATE_HOME': directory + '/state'}):
            with patch.object(provider, 'fetch_codex_quota', side_effect=RuntimeError('offline')):
                provider.refresh_quota('codex')
            with patch.object(provider.subprocess, 'Popen') as spawn:
                result = provider.get_usage('codex')
                spawn.assert_not_called()
            self.assertEqual(result['bar1_percent'], -1)
            self.assertEqual(result['bar2_percent'], -1)

    def test_partial_update_preserves_previous_weekly_value(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {
                'XDG_CACHE_HOME': directory + '/cache', 'XDG_STATE_HOME': directory + '/state'}):
            path, _ = provider.cache_paths('codex')
            provider.write_cache(path, dict(bar1_percent=60, bar2_percent=22, bar2_exact=22.4,
                                          bar2_resets_at=2000000000, timestamp=time.time()-400))
            partial = provider.unknown_quota()
            partial.update(bar1_percent=55, bar1_exact=55)
            with patch.object(provider, 'fetch_codex_quota', return_value=partial):
                provider.refresh_quota('codex')
            saved = provider.read_cache(path)
            self.assertEqual(saved['bar1_percent'], 55)
            self.assertEqual(saved['bar2_percent'], 22)
            self.assertEqual(saved['bar2_resets_at'], 2000000000)



class ActivityTests(unittest.TestCase):
    def event(self, kind, event_type='event_msg', **payload):
        return dict(timestamp='2026-10-22T17:00:00Z', type=event_type, payload=dict(type=kind, **payload))

    def status(self, events, age=1):
        now = provider.datetime.fromisoformat('2026-10-22T17:00:00+00:00').timestamp() + age
        return provider.codex_session_status(events, now)

    def test_active_tool_thinking_and_completion(self):
        events = [self.event('task_started')]
        self.assertEqual(self.status(events), 'думает')
        events.append(self.event('function_call', 'response_item', call_id='a'))
        self.assertEqual(self.status(events), 'работает')
        events.append(self.event('function_call_output', 'response_item', call_id='a'))
        self.assertEqual(self.status(events), 'думает')
        events += [self.event('task_complete'), self.event('token_count')]
        self.assertEqual(self.status(events), 'отдыхает')

    def test_truncated_tail_without_task_start_still_detects_activity(self):
        self.assertEqual(self.status([self.event('token_count')]), 'думает')
        self.assertEqual(self.status([self.event('item_completed', item={'type': 'command_execution'})]), 'работает')

    def test_old_crashed_turn_does_not_stay_busy(self):
        self.assertEqual(self.status([self.event('task_started')], age=181), 'отдыхает')

    def test_final_answer_and_abort_clear_pending_tools(self):
        events = [self.event('function_call', 'response_item', call_id='a')]
        self.assertEqual(self.status(events + [self.event('turn_aborted')]), 'отдыхает')
        self.assertEqual(self.status(events + [self.event('message', 'response_item', role='assistant', phase='final_answer')]), 'отдыхает')

    def test_tail_skips_partial_first_and_last_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'session.jsonl'
            valid = self.event('task_complete')
            path.write_bytes(b'x' * 500 + b'\n' + json.dumps(valid).encode() + b'\n{"partial":')
            self.assertEqual(list(provider.tail_events(path, 250)), [valid])


class AntigravityActivityTests(unittest.TestCase):
    def test_headless_and_interactive_requests_are_detected_without_tty(self):
        with tempfile.TemporaryDirectory() as directory:
            commands = {
                1: ['agy', '-p', 'review code'],
                2: ['/usr/bin/agy'],
                3: ['agy', '--print=review /usage parser'],
                4: ['agy', '-p', '/usage'],
                5: ['agy', '--prompt=/usage'],
                6: ['agy', 'models'],
                7: ['python3', 'status_provider.py', '--refresh-only'],
                8: ['unrelated', 'agy', '-p', 'prompt'],
                9: ['agy', '--input-format', 'stream-json'],
            }
            for pid, args in commands.items():
                path = Path(directory) / str(pid)
                path.mkdir()
                (path/'cmdline').write_bytes(('\0'.join(args)+'\0').encode())
            self.assertEqual(set(provider.get_active_agy_pids(directory)), {1, 2, 3, 9})

    def test_headless_startup_is_thinking_but_stream_waiting_is_idle(self):
        with patch.object(provider, 'inspect_pid_fds', return_value=([], None)):
            with patch.object(provider, 'process_args', return_value=['agy', '-p', 'review']):
                self.assertEqual(provider.check_single_pid_status(123, time.time()), 'думает')
            with patch.object(provider, 'process_args', return_value=['agy', '--input-format', 'stream-json']):
                self.assertEqual(provider.check_single_pid_status(123, time.time()), 'отдыхает')

    def test_long_running_steps_do_not_age_out_while_process_owns_database(self):
        import sqlite3
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'session.db'
            connection = sqlite3.connect(path)
            connection.execute('CREATE TABLE steps (idx INTEGER, step_type INTEGER, status INTEGER, metadata BLOB, step_payload BLOB)')
            for kind, state, payload, expected in [
                (14, 3, b'', 'думает'),
                (15, 2, b'', 'думает'),
                (15, 8, b'', 'думает'),
                (15, 9, b'', 'думает'),
                (999, 2, b'', 'работает'),
                (999, 3, b'', 'думает'),
                (5, 2, b'', 'работает'),
                (5, 3, b'', 'думает'),
                (5, 2, b'ask_question', 'отдыхает'),
                (15, 3, b'', 'отдыхает'),
                (15, 4, b'', 'отдыхает')]:
                connection.execute('DELETE FROM steps')
                connection.execute('INSERT INTO steps VALUES (0, ?, ?, ?, ?)', (kind,state,b'meta',payload))
                connection.commit()
                with patch.object(provider, 'parse_meta_timestamps', return_value={7: time.time()-300}):
                    self.assertEqual(provider.check_db_status(str(path),time.time()), expected)
            connection.close()

    def test_completed_planner_with_tool_calls_is_working(self):
        import sqlite3
        def varint(value):
            out = bytearray()
            while value > 127:
                out.append((value & 127) | 128)
                value >>= 7
            out.append(value)
            return bytes(out)
        def field(number, value):
            return varint(number << 3 | 2) + varint(len(value)) + value
        payload = field(20, field(7, field(2, b'view_file')))
        self.assertTrue(provider.planner_has_tool_calls(payload))
        self.assertFalse(provider.planner_has_tool_calls(field(20, field(1, b'final text mentioning tool calls'))))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'session.db'
            c = sqlite3.connect(path)
            c.execute('CREATE TABLE steps (idx INTEGER, step_type INTEGER, status INTEGER, metadata BLOB, step_payload BLOB)')
            c.execute('INSERT INTO steps VALUES (0, 15, 3, NULL, ?)', (payload,))
            c.commit(); c.close()
            self.assertEqual(provider.check_db_status(str(path), time.time()), 'работает')

    def test_completion_takes_precedence_over_headless_fallback(self):
        with patch.object(provider, 'inspect_pid_fds', return_value=(['session.db'], None)), \
             patch.object(provider, 'check_db_status', return_value='отдыхает'), \
             patch.object(provider, 'process_args', return_value=['agy', '-p', 'review']):
            self.assertEqual(provider.check_single_pid_status(123, time.time()), 'отдыхает')

    def test_shutdown_does_not_flash_thinking_after_database_closes(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory)/'cli.log'
            log.write_text('I1022 22:00:00.000000 CLI store manager shutting down')
            with patch.object(provider, 'inspect_pid_fds', return_value=([], str(log))), \
                 patch.object(provider, 'process_args', return_value=['agy', '-p', 'review']):
                self.assertEqual(provider.check_single_pid_status(123, time.time()), 'отдыхает')

    def test_parallel_sessions_and_no_process(self):
        with patch.object(provider, 'check_single_pid_status', side_effect=['отдыхает','работает','думает']):
            self.assertEqual(provider.check_agy_status([1,2,3]), 'работает')
        self.assertEqual(provider.check_agy_status([]), 'спит')


if __name__ == '__main__':
    unittest.main()
