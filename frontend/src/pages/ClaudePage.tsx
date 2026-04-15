import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { claudeApi, type ClaudeArtifactItem, type ClaudeDraft, type ClaudeLifecycleItem, type ClaudeOverview } from '../api';
import EmptyState from '../components/EmptyState';
import MetricCard from '../components/MetricCard';
import { formatDate, truncate } from '../utils/format';

export default function ClaudePage() {
  const { t } = useTranslation();
  const [overview, setOverview] = useState<ClaudeOverview | null>(null);
  const [artifacts, setArtifacts] = useState<ClaudeArtifactItem[]>([]);
  const [drafts, setDrafts] = useState<ClaudeDraft[]>([]);
  const [lifecycle, setLifecycle] = useState<ClaudeLifecycleItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [overviewResp, artifactResp, draftResp, lifecycleResp] = await Promise.all([
          claudeApi.getOverview(),
          claudeApi.listArtifacts(),
          claudeApi.listDrafts(),
          claudeApi.listLifecycle(),
        ]);
        if (!cancelled) {
          setOverview(overviewResp);
          setArtifacts(artifactResp);
          setDrafts(draftResp);
          setLifecycle(lifecycleResp);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : t('claude.failedToLoad'));
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, [t]);

  const topArtifactTypes = useMemo(
    () =>
      Object.entries(overview?.artifact_types ?? {})
        .sort((left, right) => right[1] - left[1])
        .slice(0, 6),
    [overview],
  );

  const topLifecycleStatuses = useMemo(
    () =>
      Object.entries(overview?.lifecycle_statuses ?? {})
        .sort((left, right) => right[1] - left[1])
        .slice(0, 5),
    [overview],
  );

  if (loading) {
    return <div className="p-6 text-sm text-muted">{t('claude.loading')}</div>;
  }

  if (error || !overview) {
    return <div className="p-6 text-sm text-danger">{error ?? t('claude.unavailable')}</div>;
  }

  if (!overview.enabled) {
    return (
      <div className="p-6">
        <EmptyState
          title={t('claude.notDetected')}
          description={overview.reason ?? t('claude.notDetectedDesc')}
        />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold font-serif">{t('claude.title')}</h1>
        <div className="text-sm text-muted">{t('claude.workspace', { path: overview.workspace_root })}</div>
      </div>

      <section className="metrics-row">
        <MetricCard label={t('claude.totalArtifacts')} value={overview.artifact_count} hint={t('claude.detectedInWorkspace')} />
        <MetricCard label={t('claude.totalDrafts')} value={overview.draft_count} hint={overview.draft_root ?? t('common.none')} />
        <MetricCard label={t('claude.artifactTypes')} value={Object.keys(overview.artifact_types).length} hint={t('claude.distinctTypes')} />
        <MetricCard label={t('claude.lifecycleSubjects')} value={lifecycle.length} hint={t('claude.lifecycleHint')} />
      </section>

      <section className="grid grid-cols-2 gap-6">
        <div className="panel-surface p-5 space-y-4">
          <div>
            <div className="text-xs uppercase tracking-[0.16em] text-muted">{t('claude.inventory')}</div>
            <h2 className="text-2xl font-bold font-serif mt-1">{t('claude.artifactTypeBreakdown')}</h2>
          </div>
          {topArtifactTypes.length === 0 ? (
            <EmptyState title={t('claude.noArtifacts')} description={t('claude.noArtifactsDesc')} />
          ) : (
            <div className="space-y-3">
              {topArtifactTypes.map(([type, count]) => (
                <div key={type} className="record-card block p-4">
                  <div className="flex items-center justify-between gap-4">
                    <div className="font-bold break-all">{type}</div>
                    <div className="text-2xl font-bold font-serif">{count}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="panel-surface p-5 space-y-4">
          <div>
            <div className="text-xs uppercase tracking-[0.16em] text-muted">{t('claude.governance')}</div>
            <h2 className="text-2xl font-bold font-serif mt-1">{t('claude.lifecycleStatusBreakdown')}</h2>
          </div>
          {topLifecycleStatuses.length === 0 ? (
            <EmptyState title={t('claude.noLifecycle')} description={t('claude.noLifecycleDesc')} />
          ) : (
            <div className="space-y-3">
              {topLifecycleStatuses.map(([status, count]) => (
                <div key={status} className="record-card block p-4">
                  <div className="flex items-center justify-between gap-4">
                    <div className="font-bold break-all">{status}</div>
                    <div className="text-2xl font-bold font-serif">{count}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      <section className="grid grid-cols-2 gap-6">
        <div className="panel-surface p-5 space-y-4">
          <div>
            <div className="text-xs uppercase tracking-[0.16em] text-muted">{t('claude.drafts')}</div>
            <h2 className="text-2xl font-bold font-serif mt-1">{t('claude.recentDrafts')}</h2>
          </div>
          {drafts.length === 0 ? (
            <EmptyState title={t('claude.noDrafts')} description={t('claude.noDraftsDesc')} />
          ) : (
            <div className="space-y-3">
              {drafts.slice(0, 8).map((draft) => (
                <div key={draft.absolute_path} className="record-card block p-4 space-y-2">
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0 space-y-1">
                      <div className="font-bold truncate">{draft.name}</div>
                      <div className="text-sm text-muted break-all">{draft.path}</div>
                    </div>
                    <div className="text-right shrink-0">
                      <div className="text-xs uppercase tracking-[0.16em] text-muted">{draft.bucket}</div>
                      <div className="text-xs text-muted">{formatDate(draft.modified_at)}</div>
                    </div>
                  </div>
                  <div className="text-xs text-muted break-all">{draft.absolute_path}</div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="panel-surface p-5 space-y-4">
          <div>
            <div className="text-xs uppercase tracking-[0.16em] text-muted">{t('claude.artifacts')}</div>
            <h2 className="text-2xl font-bold font-serif mt-1">{t('claude.sampleArtifacts')}</h2>
          </div>
          {artifacts.length === 0 ? (
            <EmptyState title={t('claude.noArtifacts')} description={t('claude.noArtifactsDesc')} />
          ) : (
            <div className="space-y-3">
              {artifacts.slice(0, 8).map((artifact) => (
                <div key={artifact.artifact_id} className="record-card block p-4 space-y-2">
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0 space-y-1">
                      <div className="font-bold truncate">{artifact.artifact_type}</div>
                      <div className="text-sm text-muted break-all">{artifact.path}</div>
                    </div>
                  </div>
                  <div className="text-xs text-muted">{truncate(artifact.notes || t('common.noDescription'), 180)}</div>
                  <div className="flex flex-wrap gap-2 text-xs">
                    {artifact.producers.slice(0, 3).map((producer) => (
                      <span key={`${artifact.artifact_id}-${producer}`} className="tag px-2 py-1">{producer}</span>
                    ))}
                    {artifact.consumers.slice(0, 3).map((consumer) => (
                      <span key={`${artifact.artifact_id}-${consumer}`} className="tag px-2 py-1">{consumer}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
