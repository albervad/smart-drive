from smartdrive.infrastructure.system_stats import read_system_stats


def get_dashboard_system_stats() -> dict:
    return read_system_stats()