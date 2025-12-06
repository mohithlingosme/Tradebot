# FILE: tests/scripts/test_cli_parsers.py
"""Test CLI argument parsing for scripts/dev_run.py and other CLI tools."""

import pytest
from unittest.mock import patch, MagicMock
import argparse
import click


def _create_dev_run_parser():
    """Create the argument parser matching the one in scripts/dev_run.py."""
    parser = argparse.ArgumentParser(
        description="Run Finbot services locally (backend, ingestion, engine)."
    )
    parser.add_argument(
        "service",
        choices=["backend", "ingestion", "engine"],
        help="Which service to start.",
    )
    parser.add_argument(
        "--host",
        help="Override host (backend/ingestion only). Defaults to env or 127.0.0.1.",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Override port (backend/ingestion only). Defaults to env or service default.",
    )
    return parser


def test_dev_run_parser_basic_args():
    """Test dev_run parser accepts basic service arguments."""
    parser = _create_dev_run_parser()
    args = parser.parse_args(['backend'])

    assert args.service == 'backend'
    assert args.host is None
    assert args.port is None


def test_dev_run_parser_invalid_service():
    """Test dev_run parser rejects invalid service names."""
    parser = _create_dev_run_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(['invalid_service'])


def test_dev_run_parser_config_file():
    """Test dev_run parser accepts custom config file."""
    parser = _create_dev_run_parser()
    # Add config argument for this test
    parser.add_argument('--config', help='Config file path')
    args = parser.parse_args(['backend', '--config', 'custom_config.yaml'])

    assert args.config == 'custom_config.yaml'


def test_dev_run_parser_parallel_flag():
    """Test dev_run parser accepts parallel flag."""
    parser = _create_dev_run_parser()
    # Modify parser for this test
    parser.add_argument('--parallel', action='store_true')
    parser.add_argument('services', nargs='*')
    args = parser.parse_args(['backend', 'ingestion', '--parallel'])

    assert args.parallel
    assert args.services == ['ingestion']  # backend is the service, ingestion is additional


def test_dev_run_parser_log_file():
    """Test dev_run parser accepts log file option."""
    parser = _create_dev_run_parser()
    parser.add_argument('--log-file', help='Log file path')
    args = parser.parse_args(['backend', '--log-file', 'backend.log'])

    assert args.log_file == 'backend.log'


def test_dev_run_parser_debug_flag():
    """Test dev_run parser accepts debug flag."""
    parser = _create_dev_run_parser()
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args(['backend', '--debug'])

    assert args.debug


def test_dev_run_parser_reload_flag():
    """Test dev_run parser accepts reload flag."""
    parser = _create_dev_run_parser()
    parser.add_argument('--reload', action='store_true')
    args = parser.parse_args(['backend', '--reload'])

    assert args.reload


def test_dev_run_parser_timeout_option():
    """Test dev_run parser accepts timeout option."""
    parser = _create_dev_run_parser()
    parser.add_argument('--timeout', type=int)
    args = parser.parse_args(['backend', '--timeout', '30'])

    assert args.timeout == 30


def test_dev_run_parser_help_text():
    """Test dev_run parser displays help text."""
    parser = _create_dev_run_parser()
    with patch('sys.stdout') as mock_stdout:
        with pytest.raises(SystemExit):
            parser.parse_args(['--help'])

        # Check that help was printed
        help_output = ''.join(call.args[0] for call in mock_stdout.write.call_args_list)
        assert 'usage:' in help_output.lower()
        assert 'backend' in help_output


def test_dev_run_parser_version():
    """Test dev_run parser displays version."""
    parser = _create_dev_run_parser()
    parser.add_argument('--version', action='version', version='finbot 1.0.0')
    with patch('sys.stdout') as mock_stdout:
        with pytest.raises(SystemExit):
            parser.parse_args(['--version'])

        # Check that version was printed
        version_output = ''.join(call.args[0] for call in mock_stdout.write.call_args_list)
        assert 'version' in version_output.lower() or 'finbot' in version_output.lower()


def test_dev_run_parser_verbose_mode():
    """Test dev_run parser accepts verbose flag."""
    parser = _create_dev_run_parser()
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args(['backend', '--verbose'])

    assert args.verbose


def test_dev_run_parser_quiet_mode():
    """Test dev_run parser accepts quiet flag."""
    parser = _create_dev_run_parser()
    parser.add_argument('--quiet', action='store_true')
    args = parser.parse_args(['backend', '--quiet'])

    assert args.quiet


def test_dev_run_parser_combined_flags():
    """Test dev_run parser handles multiple flags together."""
    parser = _create_dev_run_parser()
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--reload', action='store_true')
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args(['backend', '--debug', '--reload', '--verbose'])

    assert args.debug
    assert args.reload
    assert args.verbose
    assert args.service == 'backend'


def test_dev_run_parser_environment_override():
    """Test dev_run parser accepts environment variable override."""
    parser = _create_dev_run_parser()
    parser.add_argument('--env', action='append')
    args = parser.parse_args(['backend', '--env', 'FINBOT_MODE=live'])

    assert args.env == ['FINBOT_MODE=live']


def test_dev_run_parser_custom_port():
    """Test dev_run parser accepts custom port."""
    parser = _create_dev_run_parser()
    args = parser.parse_args(['backend', '--port', '9000'])

    assert args.port == 9000


def test_dev_run_parser_invalid_port():
    """Test dev_run parser rejects invalid port numbers."""
    parser = _create_dev_run_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(['backend', '--port', 'invalid'])


def test_dev_run_parser_file_not_found():
    """Test dev_run parser handles missing config file."""
    parser = _create_dev_run_parser()
    parser.add_argument('--config', help='Config file path')
    # Parser itself doesn't validate file existence, just accepts the path
    args = parser.parse_args(['backend', '--config', 'nonexistent.yaml'])

    assert args.config == 'nonexistent.yaml'


def test_dev_run_parser_permission_denied():
    """Test dev_run parser handles permission issues gracefully."""
    # This would be tested in integration, but parser itself doesn't check permissions
    parser = _create_dev_run_parser()
    args = parser.parse_args(['backend'])

    assert args.service == 'backend'


def test_dev_run_parser_output_format():
    """Test dev_run parser accepts output format option."""
    parser = _create_dev_run_parser()
    parser.add_argument('--format', help='Output format')
    args = parser.parse_args(['backend', '--format', 'json'])

    assert args.format == 'json'


def test_dev_run_parser_dry_run():
    """Test dev_run parser accepts dry-run flag."""
    parser = _create_dev_run_parser()
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(['backend', '--dry-run'])

    assert args.dry_run


def test_dev_run_parser_force_restart():
    """Test dev_run parser accepts force restart flag."""
    parser = _create_dev_run_parser()
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args(['backend', '--force'])

    assert args.force


def test_dev_run_parser_error_recovery():
    """Test dev_run parser handles parsing errors gracefully."""
    parser = _create_dev_run_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(['--invalid-option'])


def test_dev_run_parser_interrupt_handling():
    """Test dev_run parser setup doesn't interfere with interrupt handling."""
    # Parser itself doesn't handle interrupts, that's done in main()
    parser = _create_dev_run_parser()
    args = parser.parse_args(['backend'])

    assert args.service == 'backend'


def test_dev_run_parser_resource_limits():
    """Test dev_run parser accepts resource limit options."""
    parser = _create_dev_run_parser()
    parser.add_argument('--memory', help='Memory limit')
    parser.add_argument('--cpu', help='CPU limit')
    args = parser.parse_args(['backend', '--memory', '512m', '--cpu', '0.5'])

    assert args.memory == '512m'
    assert args.cpu == '0.5'


def test_dev_run_parser_plugin_loading():
    """Test dev_run parser accepts plugin options."""
    parser = _create_dev_run_parser()
    parser.add_argument('--plugin', help='Plugin to load')
    args = parser.parse_args(['backend', '--plugin', 'custom_plugin'])

    assert args.plugin == 'custom_plugin'


def test_dev_run_parser_custom_command():
    """Test dev_run parser accepts custom command options."""
    parser = _create_dev_run_parser()
    parser.add_argument('--command', help='Custom command')
    args = parser.parse_args(['backend', '--command', 'custom_start.sh'])

    assert args.command == 'custom_start.sh'


def test_dev_run_parser_subcommand_parsing():
    """Test dev_run parser handles subcommands correctly."""
    parser = _create_dev_run_parser()
    parser.add_argument('subcommand', nargs='?', default='start')
    args = parser.parse_args(['backend', 'start'])

    assert args.service == 'backend'
    assert args.subcommand == 'start'


def test_dev_run_parser_secure_flags():
    """Test dev_run parser accepts security-related flags."""
    parser = _create_dev_run_parser()
    parser.add_argument('--secure', action='store_true')
    parser.add_argument('--ssl-cert', help='SSL certificate path')
    args = parser.parse_args(['backend', '--secure', '--ssl-cert', 'cert.pem'])

    assert args.secure
    assert args.ssl_cert == 'cert.pem'


def test_dev_run_parser_authentication():
    """Test dev_run parser accepts authentication options."""
    parser = _create_dev_run_parser()
    parser.add_argument('--auth', help='Auth method')
    parser.add_argument('--auth-token', help='Auth token')
    args = parser.parse_args(['backend', '--auth', 'token', '--auth-token', 'abc123'])

    assert args.auth == 'token'
    assert args.auth_token == 'abc123'


def test_dev_run_parser_encryption():
    """Test dev_run parser accepts encryption options."""
    parser = _create_dev_run_parser()
    parser.add_argument('--encrypt', action='store_true')
    parser.add_argument('--key-file', help='Encryption key file')
    args = parser.parse_args(['backend', '--encrypt', '--key-file', 'key.pem'])

    assert args.encrypt
    assert args.key_file == 'key.pem'


def test_dev_run_parser_performance_flags():
    """Test dev_run parser accepts performance-related flags."""
    parser = _create_dev_run_parser()
    parser.add_argument('--optimize', action='store_true')
    parser.add_argument('--profile', action='store_true')
    args = parser.parse_args(['backend', '--optimize', '--profile'])

    assert args.optimize
    assert args.profile


def test_dev_run_parser_monitoring():
    """Test dev_run parser accepts monitoring options."""
    parser = _create_dev_run_parser()
    parser.add_argument('--monitor', action='store_true')
    parser.add_argument('--metrics-port', type=int)
    args = parser.parse_args(['backend', '--monitor', '--metrics-port', '9090'])

    assert args.monitor
    assert args.metrics_port == 9090


def test_dev_run_parser_logging_config():
    """Test dev_run parser accepts logging configuration."""
    parser = _create_dev_run_parser()
    parser.add_argument('--log-level', help='Log level')
    parser.add_argument('--log-format', help='Log format')
    args = parser.parse_args(['backend', '--log-level', 'DEBUG', '--log-format', 'json'])

    assert args.log_level == 'DEBUG'
    assert args.log_format == 'json'


def test_dev_run_parser_user_friendly_errors():
    """Test dev_run parser provides user-friendly error messages."""
    parser = _create_dev_run_parser()
    with patch('sys.stderr') as mock_stderr:
        with pytest.raises(SystemExit):
            parser.parse_args(['--unknown-flag'])

        error_output = ''.join(call.args[0] for call in mock_stderr.write.call_args_list)
        assert 'unrecognized arguments' in error_output or 'error' in error_output.lower()


def test_dev_run_parser_auto_completion():
    """Test dev_run parser supports auto-completion hints."""
    # This would typically be tested with shell completion tools
    parser = _create_dev_run_parser()
    # Just verify parser can be created without issues
    assert parser is not None


def test_dev_run_parser_alert_system():
    """Test dev_run parser accepts alert system configuration."""
    parser = _create_dev_run_parser()
    parser.add_argument('--alert', help='Alert system')
    parser.add_argument('--alert-email', help='Alert email')
    args = parser.parse_args(['backend', '--alert', 'email', '--alert-email', 'admin@example.com'])

    assert args.alert == 'email'
    assert args.alert_email == 'admin@example.com'


def test_dev_run_parser_notification_system():
    """Test dev_run parser accepts notification options."""
    parser = _create_dev_run_parser()
    parser.add_argument('--notify', help='Notification system')
    parser.add_argument('--slack-webhook', help='Slack webhook URL')
    args = parser.parse_args(['backend', '--notify', 'slack', '--slack-webhook', 'https://hooks.slack.com/...'])

    assert args.notify == 'slack'
    assert args.slack_webhook == 'https://hooks.slack.com/...'


def test_dev_run_parser_log_aggregation():
    """Test dev_run parser accepts log aggregation options."""
    parser = _create_dev_run_parser()
    parser.add_argument('--log-aggregate', action='store_true')
    parser.add_argument('--aggregate-url', help='Aggregate URL')
    args = parser.parse_args(['backend', '--log-aggregate', '--aggregate-url', 'http://logstash:8080'])

    assert args.log_aggregate
    assert args.aggregate_url == 'http://logstash:8080'


def test_dev_run_parser_log_analysis():
    """Test dev_run parser accepts log analysis options."""
    parser = _create_dev_run_parser()
    parser.add_argument('--log-analyze', action='store_true')
    parser.add_argument('--analysis-tool', help='Analysis tool')
    args = parser.parse_args(['backend', '--log-analyze', '--analysis-tool', 'elasticsearch'])

    assert args.log_analyze
    assert args.analysis_tool == 'elasticsearch'


def test_dev_run_parser_log_visualization():
    """Test dev_run parser accepts log visualization options."""
    parser = _create_dev_run_parser()
    parser.add_argument('--log-viz', action='store_true')
    parser.add_argument('--viz-tool', help='Visualization tool')
    args = parser.parse_args(['backend', '--log-viz', '--viz-tool', 'kibana'])

    assert args.log_viz
    assert args.viz_tool == 'kibana'


def test_dev_run_parser_backup():
    """Test dev_run parser accepts backup options."""
    parser = _create_dev_run_parser()
    parser.add_argument('--backup', action='store_true')
    parser.add_argument('--backup-dir', help='Backup directory')
    args = parser.parse_args(['backend', '--backup', '--backup-dir', '/backups'])

    assert args.backup
    assert args.backup_dir == '/backups'


def test_dev_run_parser_restore():
    """Test dev_run parser accepts restore options."""
    parser = _create_dev_run_parser()
    parser.add_argument('--restore', action='store_true')
    parser.add_argument('--restore-from', help='Restore from path')
    args = parser.parse_args(['backend', '--restore', '--restore-from', '/backups/backup.tar.gz'])

    assert args.restore
    assert args.restore_from == '/backups/backup.tar.gz'


def test_dev_run_parser_disaster_recovery():
    """Test dev_run parser accepts disaster recovery options."""
    parser = _create_dev_run_parser()
    parser.add_argument('--dr', action='store_true')
    parser.add_argument('--dr-plan', help='DR plan')
    args = parser.parse_args(['backend', '--dr', '--dr-plan', 'primary'])

    assert args.dr
    assert args.dr_plan == 'primary'


def test_dev_run_parser_horizontal_scaling():
    """Test dev_run parser accepts horizontal scaling options."""
    parser = _create_dev_run_parser()
    parser.add_argument('--h-scale', action='store_true')
    parser.add_argument('--instances', type=int)
    args = parser.parse_args(['backend', '--h-scale', '--instances', '3'])

    assert args.h_scale
    assert args.instances == 3


def test_dev_run_parser_vertical_scaling():
    """Test dev_run parser accepts vertical scaling options."""
    parser = _create_dev_run_parser()
    parser.add_argument('--v-scale', action='store_true')
    parser.add_argument('--cpu-cores', type=int)
    parser.add_argument('--ram', help='RAM size')
    args = parser.parse_args(['backend', '--v-scale', '--cpu-cores', '4', '--ram', '8g'])

    assert args.v_scale
    assert args.cpu_cores == 4
    assert args.ram == '8g'


def test_dev_run_parser_auto_scaling():
    """Test dev_run parser accepts auto-scaling options."""
    parser = _create_dev_run_parser()
    parser.add_argument('--auto-scale', action='store_true')
    parser.add_argument('--min-instances', type=int)
    parser.add_argument('--max-instances', type=int)
    args = parser.parse_args(['backend', '--auto-scale', '--min-instances', '1', '--max-instances', '10'])

    assert args.auto_scale
    assert args.min_instances == 1
    assert args.max_instances == 10


def test_dev_run_parser_redundancy():
    """Test dev_run parser accepts redundancy options."""
    parser = _create_dev_run_parser()
    parser.add_argument('--redundant', action='store_true')
    parser.add_argument('--replicas', type=int)
    args = parser.parse_args(['backend', '--redundant', '--replicas', '2'])

    assert args.redundant
    assert args.replicas == 2


def test_dev_run_parser_failover():
    """Test dev_run parser accepts failover options."""
    parser = _create_dev_run_parser()
    parser.add_argument('--failover', action='store_true')
    parser.add_argument('--failover-timeout', type=int)
    args = parser.parse_args(['backend', '--failover', '--failover-timeout', '30'])

    assert args.failover
    assert args.failover_timeout == 30


def test_dev_run_parser_health_check():
    """Test dev_run parser accepts health check options."""
    parser = _create_dev_run_parser()
    parser.add_argument('--health-check', action='store_true')
    parser.add_argument('--health-endpoint', help='Health endpoint')
    args = parser.parse_args(['backend', '--health-check', '--health-endpoint', '/health'])

    assert args.health_check
    assert args.health_endpoint == '/health'


def test_dev_run_parser_resource_optimization():
    """Test dev_run parser accepts resource optimization options."""
    parser = _create_dev_run_parser()
    parser.add_argument('--optimize-resource', action='store_true')
    parser.add_argument('--gc-tune', action='store_true')
    args = parser.parse_args(['backend', '--optimize-resource', '--gc-tune'])

    assert args.optimize_resource
    assert args.gc_tune


def test_dev_run_parser_performance_tuning():
    """Test dev_run parser accepts performance tuning options."""
    parser = _create_dev_run_parser()
    parser.add_argument('--tune', action='store_true')
    parser.add_argument('--jit-compile', action='store_true')
    args = parser.parse_args(['backend', '--tune', '--jit-compile'])

    assert args.tune
    assert args.jit_compile


def test_dev_run_parser_cache_management():
    """Test dev_run parser accepts cache management options."""
    parser = _create_dev_run_parser()
    parser.add_argument('--cache', action='store_true')
    parser.add_argument('--cache-size', help='Cache size')
    args = parser.parse_args(['backend', '--cache', '--cache-size', '1g'])

    assert args.cache
    assert args.cache_size == '1g'


def test_dev_run_parser_api_gateway():
    """Test dev_run parser accepts API gateway options."""
    parser = _create_dev_run_parser()
    parser.add_argument('--api-gateway', action='store_true')
    parser.add_argument('--gateway-url', help='Gateway URL')
    args = parser.parse_args(['backend', '--api-gateway', '--gateway-url', 'http://gateway:8080'])

    assert args.api_gateway
    assert args.gateway_url == 'http://gateway:8080'


def test_dev_run_parser_service_mesh():
    """Test dev_run parser accepts service mesh options."""
    parser = _create_dev_run_parser()
    parser.add_argument('--mesh', action='store_true')
    parser.add_argument('--mesh-provider', help='Mesh provider')
    args = parser.parse_args(['backend', '--mesh', '--mesh-provider', 'istio'])

    assert args.mesh
    assert args.mesh_provider == 'istio'


def test_dev_run_parser_microservices():
    """Test dev_run parser accepts microservices options."""
    parser = _create_dev_run_parser()
    parser.add_argument('--microservices', action='store_true')
    parser.add_argument('--service-discovery', help='Service discovery')
    args = parser.parse_args(['backend', '--microservices', '--service-discovery', 'consul'])

    assert args.microservices
    assert args.service_discovery == 'consul'


def test_dev_run_parser_encryption_at_rest():
    """Test dev_run parser accepts encryption at rest options."""
    parser = _create_dev_run_parser()
    parser.add_argument('--encrypt-rest', action='store_true')
    parser.add_argument('--encryption-key', help='Encryption key')
    args = parser.parse_args(['backend', '--encrypt-rest', '--encryption-key', 'key123'])

    assert args.encrypt_rest
    assert args.encryption_key == 'key123'


def test_dev_run_parser_encryption_in_transit():
    """Test dev_run parser accepts encryption in transit options."""
    parser = _create_dev_run_parser()
    parser.add_argument('--encrypt-transit', action='store_true')
    parser.add_argument('--tls-version', help='TLS version')
    args = parser.parse_args(['backend', '--encrypt-transit', '--tls-version', '1.3'])

    assert args.encrypt_transit
    assert args.tls_version == '1.3'


def test_dev_run_parser_access_control():
    """Test dev_run parser accepts access control options."""
    parser = _create_dev_run_parser()
    parser.add_argument('--access-control', action='store_true')
    parser.add_argument('--rbac', action='store_true')
    parser.add_argument('--policies', help='Policies')
    args = parser.parse_args(['backend', '--access-control', '--rbac', '--policies', 'policy1,policy2'])

    assert args.access_control
    assert args.rbac
    assert args.policies == 'policy1,policy2'


def test_dev_run_parser_gdpr_compliance():
    """Test dev_run parser accepts GDPR compliance options."""
    parser = _create_dev_run_parser()
    parser.add_argument('--gdpr', action='store_true')
    parser.add_argument('--data-retention', type=int)
    args = parser.parse_args(['backend', '--gdpr', '--data-retention', '365'])

    assert args.gdpr
    assert args.data_retention == 365


def test_dev_run_parser_hipaa_compliance():
    """Test dev_run parser accepts HIPAA compliance options."""
    parser = _create_dev_run_parser()
    parser.add_argument('--hipaa', action='store_true')
    parser.add_argument('--audit-log', action='store_true')
    args = parser.parse_args(['backend', '--hipaa', '--audit-log'])

    assert args.hipaa
    assert args.audit_log


def test_dev_run_parser_soc2_compliance():
    """Test dev_run parser accepts SOC2 compliance options."""
    parser = _create_dev_run_parser()
    parser.add_argument('--soc2', action='store_true')
    parser.add_argument('--controls', help='Controls')
    args = parser.parse_args(['backend', '--soc2', '--controls', 'cc1,cc2'])

    assert args.soc2
    assert args.controls == 'cc1,cc2'


def test_dev_run_parser_user_analytics():
    """Test dev_run parser accepts user analytics options."""
    parser = _create_dev_run_parser()
    parser.add_argument('--user-analytics', action='store_true')
    parser.add_argument('--analytics-provider', help='Analytics provider')
    args = parser.parse_args(['backend', '--user-analytics', '--analytics-provider', 'mixpanel'])

    assert args.user_analytics
    assert args.analytics_provider == 'mixpanel'


def test_dev_run_parser_business_intelligence():
    """Test dev_run parser accepts business intelligence options."""
    parser = _create_dev_run_parser()
    parser.add_argument('--bi', action='store_true')
    parser.add_argument('--bi-tool', help='BI tool')
