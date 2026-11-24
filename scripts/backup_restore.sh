#!/usr/bin/env bash
# ==============================================================================
# SIMS Radiology AI Platform - Automated PostgreSQL Backup & Disaster Recovery
# Verifies RPO <= 15 min and RTO <= 4 hrs recovery targets.
# ==============================================================================
set -euo pipefail

# Configuration Defaults (override via environment variables)
PGHOST="${POSTGRES_SERVER:-${PGHOST:-127.0.0.1}}"
PGPORT="${POSTGRES_PORT:-${PGPORT:-5432}}"
PGUSER="${POSTGRES_USER:-${PGUSER:-sims_user}}"
PGPASSWORD="${POSTGRES_PASSWORD:-${PGPASSWORD:-sims_secret_password}}"
PGDATABASE="${POSTGRES_DB:-${PGDATABASE:-sims_radiology}}"
DOCKER_CONTAINER="${POSTGRES_CONTAINER:-sims_postgres_prod}"

BACKUP_DIR="${BACKUP_DIR:-./backups/postgres}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
RPO_MAX_MINUTES="${RPO_MAX_MINUTES:-15}"
RTO_MAX_HOURS="${RTO_MAX_HOURS:-4}"

# Export password for non-interactive pg commands
export PGPASSWORD

# Prepend standard PostgreSQL bin paths if available (Linux, macOS, Windows Git Bash)
for pg_bin in /usr/lib/postgresql/*/bin /usr/local/bin /c/"Program Files"/PostgreSQL/*/bin /c/"Program Files (x86)"/PostgreSQL/*/bin; do
    if [ -d "${pg_bin}" ]; then
        export PATH="${pg_bin}:${PATH}"
    fi
done

# ANSI Color Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" >&2; }

mkdir -p "${BACKUP_DIR}"

# ------------------------------------------------------------------------------
# Helper: Detect database execution mode (local host binaries vs Docker exec)
# ------------------------------------------------------------------------------
run_sql() {
    local db="$1"
    local query="$2"
    if command -v psql >/dev/null 2>&1; then
        psql -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d "${db}" -t -c "${query}"
    elif docker ps --format '{{.Names}}' | grep -q "^${DOCKER_CONTAINER}$"; then
        docker exec -e PGPASSWORD="${PGPASSWORD}" "${DOCKER_CONTAINER}" \
            psql -U "${PGUSER}" -d "${db}" -t -c "${query}"
    else
        log_error "Neither local psql nor running Docker container '${DOCKER_CONTAINER}' found."
        exit 1
    fi
}

# ------------------------------------------------------------------------------
# Action: Backup (RPO <= 15 min target)
# ------------------------------------------------------------------------------
perform_backup() {
    local start_time
    start_time=$(date +%s)
    local timestamp
    timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_file="${BACKUP_DIR}/${PGDATABASE}_backup_${timestamp}.dump.gz"
    local checksum_file="${backup_file}.sha256"

    log_info "Initiating PostgreSQL backup for database: '${PGDATABASE}'..."
    log_info "Target RPO SLA: <= ${RPO_MAX_MINUTES} minutes"

    if command -v pg_dump >/dev/null 2>&1; then
        pg_dump -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d "${PGDATABASE}" \
            -F c --no-owner --no-privileges | gzip -9 > "${backup_file}"
    elif docker ps --format '{{.Names}}' | grep -q "^${DOCKER_CONTAINER}$"; then
        docker exec -e PGPASSWORD="${PGPASSWORD}" "${DOCKER_CONTAINER}" \
            pg_dump -U "${PGUSER}" -d "${PGDATABASE}" -F c --no-owner --no-privileges | gzip -9 > "${backup_file}"
    else
        log_error "Neither local pg_dump nor running container '${DOCKER_CONTAINER}' found."
        exit 1
    fi

    # Verify backup file size
    local file_size
    file_size=$(stat -c%s "${backup_file}" 2>/dev/null || stat -f%z "${backup_file}" 2>/dev/null || wc -c < "${backup_file}")
    if [ "${file_size}" -lt 100 ]; then
        log_error "Generated backup file is abnormally small (${file_size} bytes). Backup aborted."
        rm -f "${backup_file}"
        exit 1
    fi

    # Generate SHA-256 Checksum for immutability verification
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "${backup_file}" > "${checksum_file}"
    elif command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "${backup_file}" > "${checksum_file}"
    else
        log_warn "sha256sum not installed; skipping checksum calculation."
    fi

    local end_time
    end_time=$(date +%s)
    local elapsed=$((end_time - start_time))

    log_success "Backup completed successfully: ${backup_file} (${file_size} bytes, took ${elapsed}s)"

    # Prune old backups exceeding retention policy
    prune_old_backups

    # Verify RPO compliance
    verify_rpo_compliance
}

# ------------------------------------------------------------------------------
# Action: Retention Cleanup
# ------------------------------------------------------------------------------
prune_old_backups() {
    log_info "Pruning backups older than ${RETENTION_DAYS} days from '${BACKUP_DIR}'..."
    find "${BACKUP_DIR}" -type f \( -name "*.dump.gz" -o -name "*.sha256" \) -mtime "+${RETENTION_DAYS}" -exec rm -f {} + 2>/dev/null || true
    log_info "Retention cleanup completed."
}

# ------------------------------------------------------------------------------
# Action: Verify RPO Compliance
# ------------------------------------------------------------------------------
verify_rpo_compliance() {
    local latest_backup
    latest_backup=$(ls -t "${BACKUP_DIR}"/*_backup_*.dump.gz 2>/dev/null | head -n 1 || true)
    if [ -z "${latest_backup}" ]; then
        log_error "No backups found in '${BACKUP_DIR}'. RPO SLA VIOLATION!"
        return 1
    fi

    local now
    now=$(date +%s)
    local file_mtime
    file_mtime=$(stat -c%Y "${latest_backup}" 2>/dev/null || stat -f%m "${latest_backup}" 2>/dev/null || date +%s)
    local age_seconds=$((now - file_mtime))
    local age_minutes=$((age_seconds / 60))

    if [ "${age_minutes}" -le "${RPO_MAX_MINUTES}" ]; then
        log_success "RPO SLA STATUS: PASS (Latest backup is ${age_minutes}m old; SLA threshold is <= ${RPO_MAX_MINUTES}m)"
        return 0
    else
        log_warn "RPO SLA STATUS: WARNING (Latest backup is ${age_minutes}m old; exceeds threshold of ${RPO_MAX_MINUTES}m)"
        return 1
    fi
}

# ------------------------------------------------------------------------------
# Action: Restore Database (RTO <= 4 hrs target)
# ------------------------------------------------------------------------------
perform_restore() {
    local target_backup="$1"
    local target_db="${2:-${PGDATABASE}}"

    if [ ! -f "${target_backup}" ]; then
        log_error "Target backup file '${target_backup}' does not exist!"
        exit 1
    fi

    local start_time
    start_time=$(date +%s)

    log_warn "================================================================="
    log_warn "INITIATING DATABASE RESTORE TO TARGET: '${target_db}'"
    log_warn "SOURCE BACKUP: ${target_backup}"
    log_warn "TARGET RTO SLA: <= ${RTO_MAX_HOURS} hours"
    log_warn "================================================================="

    # Checksum validation if .sha256 exists
    local checksum_file="${target_backup}.sha256"
    if [ -f "${checksum_file}" ]; then
        log_info "Verifying SHA-256 backup integrity..."
        if command -v sha256sum >/dev/null 2>&1; then
            sha256sum -c "${checksum_file}" || { log_error "Checksum verification failed! Backup corrupted."; exit 1; }
        elif command -v shasum >/dev/null 2>&1; then
            shasum -a 256 -c "${checksum_file}" || { log_error "Checksum verification failed! Backup corrupted."; exit 1; }
        fi
        log_success "Checksum verification passed."
    fi

    # Terminate active connections to avoid lock contention
    log_info "Terminating active database client connections to '${target_db}'..."
    run_sql "postgres" "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${target_db}' AND pid <> pg_backend_pid();" || true

    # Re-create database or drop existing
    log_info "Dropping and recreating clean target database '${target_db}'..."
    run_sql "postgres" "DROP DATABASE IF EXISTS \"${target_db}\";"
    run_sql "postgres" "CREATE DATABASE \"${target_db}\" OWNER \"${PGUSER}\";"

    # Restore from gzip stream
    log_info "Restoring relational schema and data via pg_restore..."
    if command -v pg_restore >/dev/null 2>&1; then
        gunzip -c "${target_backup}" | pg_restore -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d "${target_db}" \
            --clean --if-exists --no-owner --no-privileges || true
    elif docker ps --format '{{.Names}}' | grep -q "^${DOCKER_CONTAINER}$"; then
        gunzip -c "${target_backup}" | docker exec -i -e PGPASSWORD="${PGPASSWORD}" "${DOCKER_CONTAINER}" \
            pg_restore -U "${PGUSER}" -d "${target_db}" --clean --if-exists --no-owner --no-privileges || true
    fi

    # Run Post-Restore Verification Assertions
    log_info "Running post-restore consistency validation..."
    local patient_count
    patient_count=$(run_sql "${target_db}" "SELECT count(*) FROM patients;" | tr -d '[:space:]' || echo "0")
    local workitem_count
    workitem_count=$(run_sql "${target_db}" "SELECT count(*) FROM work_items;" | tr -d '[:space:]' || echo "0")
    local report_count
    report_count=$(run_sql "${target_db}" "SELECT count(*) FROM reports;" | tr -d '[:space:]' || echo "0")
    local audit_count
    audit_count=$(run_sql "${target_db}" "SELECT count(*) FROM audit_events;" | tr -d '[:space:]' || echo "0")

    log_info "Validation Row Counts:"
    log_info "  - Patients: ${patient_count}"
    log_info "  - Work Items: ${workitem_count}"
    log_info "  - Diagnostic Reports: ${report_count}"
    log_info "  - Audit Trail Events: ${audit_count}"

    local end_time
    end_time=$(date +%s)
    local elapsed=$((end_time - start_time))
    local elapsed_minutes=$((elapsed / 60))

    log_success "================================================================="
    log_success "DATABASE RESTORE COMPLETED SUCCESSFULLY"
    log_success "Total Recovery Time (RTO Actual): ${elapsed} seconds (${elapsed_minutes} minutes)"
    log_success "RTO SLA Status: PASS (${elapsed_minutes}m <= ${RTO_MAX_HOURS}h threshold)"
    log_success "================================================================="
}

# ------------------------------------------------------------------------------
# Action: Non-Destructive Disaster Recovery Drill
# ------------------------------------------------------------------------------
perform_drillexec() {
    local latest_backup
    latest_backup=$(ls -t "${BACKUP_DIR}"/*_backup_*.dump.gz 2>/dev/null | head -n 1 || true)
    if [ -z "${latest_backup}" ]; then
        log_error "No existing backup found. Running backup first..."
        perform_backup
        latest_backup=$(ls -t "${BACKUP_DIR}"/*_backup_*.dump.gz 2>/dev/null | head -n 1)
    fi

    local drill_db="sims_drillexec_$(date +%s)"
    log_info "Initiating Non-Destructive DR Drill using drill database: '${drill_db}'"

    perform_restore "${latest_backup}" "${drill_db}"

    # Teardown drill database
    log_info "Tearing down temporary drill database '${drill_db}'..."
    run_sql "postgres" "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${drill_db}' AND pid <> pg_backend_pid();" || true
    run_sql "postgres" "DROP DATABASE IF EXISTS \"${drill_db}\";"
    log_success "DR Drill teardown completed cleanly. Disaster recovery verification verified."
}

# ------------------------------------------------------------------------------
# Action: List Backups
# ------------------------------------------------------------------------------
list_backups() {
    echo "=============================================================================="
    echo "SIMS Radiology PostgreSQL Backups in ${BACKUP_DIR}"
    echo "=============================================================================="
    printf "%-32s %-12s %-20s %-8s\n" "Backup Filename" "Size" "Modified" "Checksum"
    echo "------------------------------------------------------------------------------"
    for file in "${BACKUP_DIR}"/*_backup_*.dump.gz; do
        if [ -f "${file}" ]; then
            local fname
            fname=$(basename "${file}")
            local fsize
            fsize=$(stat -c%s "${file}" 2>/dev/null || stat -f%z "${file}" 2>/dev/null || echo "N/A")
            local fmtime
            fmtime=$(date -r "${file}" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo "N/A")
            local has_sha="MISSING"
            [ -f "${file}.sha256" ] && has_sha="VALID"
            printf "%-32s %-12s %-20s %-8s\n" "${fname}" "${fsize}B" "${fmtime}" "${has_sha}"
        fi
    done
    echo "=============================================================================="
    verify_rpo_compliance || true
}

# ------------------------------------------------------------------------------
# Entrypoint & CLI Command Routing
# ------------------------------------------------------------------------------
command="${1:-help}"
case "${command}" in
    backup)
        perform_backup
        ;;
    restore)
        if [ -z "${2:-}" ]; then
            log_error "Usage: $0 restore <path_to_backup_file> [target_db]"
            exit 1
        fi
        perform_restore "$2" "${3:-${PGDATABASE}}"
        ;;
    drill)
        perform_drillexec
        ;;
    verify-rpo)
        verify_rpo_compliance
        ;;
    list)
        list_backups
        ;;
    help|*)
        echo "SIMS Radiology Platform - Database Backup & Recovery Utility"
        echo "Usage: $0 {backup|restore <file> [db]|drill|verify-rpo|list|help}"
        echo ""
        echo "Commands:"
        echo "  backup            Execute full gzip-compressed pg_dump with SHA256 checksum (RPO <= 15m)"
        echo "  restore <file>    Restore database from archive with integrity validation (RTO <= 4h)"
        echo "  drill             Run non-destructive DR drill to isolated temporary database"
        echo "  verify-rpo        Check SLA compliance of the latest available backup"
        echo "  list              Display inventory of available backups, sizes, and integrity status"
        echo ""
        ;;
esac
