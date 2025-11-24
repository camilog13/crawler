import {
  getProject,
  getCrawls,
  getLatestCrawlSummary,
  getIssuesByType
} from "@/lib/api";
import type { IssueTypeGroup } from "@/lib/types";
import Card from "@/components/ui/Card";
import HealthBar from "@/components/ui/HealthBar";
import SeverityPill from "@/components/ui/SeverityPill";
import CategoryPill from "@/components/ui/CategoryPill";
import IssuesBySeverityChart from "@/components/charts/IssuesBySeverityChart";
import IssuesByCategoryChart from "@/components/charts/IssuesByCategoryChart";
import Link from "next/link";
import AuthGuard from "@/components/auth/AuthGuard";

export default async function ProjectDashboardPage({
  params
}: {
  params: { projectId: string };
}) {
  const projectId = params.projectId;
  const project = await getProject(projectId);
  const crawls = await getCrawls(projectId);

  if (!crawls.length) {
    return (
      <AuthGuard>
        <div className="space-y-4">
          <h1 className="text-xl font-semibold">{project.name}</h1>
          <p className="text-sm text-slate-400">
            Aún no hay crawls registrados para este proyecto.
          </p>
        </div>
      </AuthGuard>
    );
  }

  const latestCrawl = crawls[0];
  const summary = await getLatestCrawlSummary(projectId);
  const issuesByType: IssueTypeGroup[] = await getIssuesByType(latestCrawl.id);

  return (
    <AuthGuard>
      <div className="space-y-6">
        <div className="flex flex-wrap justify-between gap-4 items-center">
          <div>
            <h1 className="text-xl font-semibold">{project.name}</h1>
            <p className="text-sm text-slate-400">{project.domain}</p>
          </div>
          <div className="text-xs text-slate-400">
            Último crawl:{" "}
            <span className="font-semibold text-slate-200">
              {new Date(latestCrawl.started_at).toLocaleString()}
            </span>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-4">
          <Card className="md:col-span-2">
            <HealthBar value={summary.site_health} />
            <p className="mt-3 text-xs text-slate-400">
              Salud general basada en número de issues ponderados por severidad y total de URLs.
            </p>
          </Card>
          <Card>
            <div className="text-xs text-slate-400">Total URLs rastreadas</div>
            <div className="mt-1 text-2xl font-semibold">
              {summary.total_urls.toLocaleString()}
            </div>
            <p className="mt-2 text-xs text-slate-500">
              Incluye todas las URLs rastreadas en el último crawl.
            </p>
          </Card>
          <Card>
            <div className="text-xs text-slate-400">Total issues detectados</div>
            <div className="mt-1 text-2xl font-semibold">
              {summary.total_issues.toLocaleString()}
            </div>
            <p className="mt-2 text-xs text-slate-500">
              Agrupados por tipo de issue, severidad y categoría.
            </p>
          </Card>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <div className="flex justify-between items-center mb-2">
              <h2 className="text-sm font-semibold">Issues por severidad</h2>
            </div>
            <IssuesBySeverityChart summary={summary} />
          </Card>
          <Card>
            <div className="flex justify-between items-center mb-2">
              <h2 className="text-sm font-semibold">Issues por categoría</h2>
            </div>
            <IssuesByCategoryChart summary={summary} />
          </Card>
        </div>

        <Card>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-sm font-semibold">Issues por tipo</h2>
            <span className="text-xs text-slate-500">
              Haz clic en “Ver URLs” para instrucciones por página.
            </span>
          </div>
          <div className="overflow-auto scrollbar-thin">
            <table className="min-w-full text-xs">
              <thead className="bg-slate-900/60">
                <tr>
                  <th className="px-3 py-2 text-left font-medium text-slate-400">
                    Issue
                  </th>
                  <th className="px-3 py-2 text-left font-medium text-slate-400">
                    Categoría
                  </th>
                  <th className="px-3 py-2 text-left font-medium text-slate-400">
                    Severidad
                  </th>
                  <th className="px-3 py-2 text-right font-medium text-slate-400">
                    # URLs
                  </th>
                  <th className="px-3 py-2 text-right font-medium text-slate-400">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {issuesByType.map((it) => (
                  <tr key={it.code} className="hover:bg-slate-900/40">
                    <td className="px-3 py-2">
                      <div className="font-medium text-slate-100 text-xs">
                        {it.name}
                      </div>
                      <div className="text-[11px] text-slate-500 break-all">
                        {it.code}
                      </div>
                    </td>
                    <td className="px-3 py-2">
                      <CategoryPill category={it.category} />
                    </td>
                    <td className="px-3 py-2">
                      <SeverityPill severity={it.severity} />
                    </td>
                    <td className="px-3 py-2 text-right text-slate-100">
                      {it.count.toLocaleString()}
                    </td>
                    <td className="px-3 py-2 text-right">
                      <Link
                        href={`/projects/${projectId}/issues/${it.code}`}
                        className="text-xs text-seoAccent hover:underline"
                      >
                        Ver URLs →
                      </Link>
                    </td>
                  </tr>
                ))}
                {issuesByType.length === 0 && (
                  <tr>
                    <td
                      colSpan={5}
                      className="px-3 py-4 text-center text-slate-500 text-xs"
                    >
                      Este crawl todavía no tiene issues generados.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </AuthGuard>
  );
}
