import { getProject, getCrawls, getIssuesForType } from "@/lib/api";
import type { Issue, IssueDetailsPayload } from "@/lib/types";
import Card from "@/components/ui/Card";
import SeverityPill from "@/components/ui/SeverityPill";
import CategoryPill from "@/components/ui/CategoryPill";
import IssueTable from "./IssueTable";
import AuthGuard from "@/components/auth/AuthGuard";

export default async function IssueTypePage({
  params
}: {
  params: { projectId: string; issueCode: string };
}) {
  const { projectId, issueCode } = params;
  const project = await getProject(projectId);
  const crawls = await getCrawls(projectId);

  if (!crawls.length) {
    return (
      <AuthGuard>
        <div className="space-y-4">
          <h1 className="text-lg font-semibold">
            {project.name} – {issueCode}
          </h1>
          <p className="text-sm text-slate-400">
            Aún no hay crawls para este proyecto.
          </p>
        </div>
      </AuthGuard>
    );
  }

  const latestCrawl = crawls[0];
  const issues: Issue[] = await getIssuesForType(latestCrawl.id, issueCode);

  if (!issues.length) {
    return (
      <AuthGuard>
        <div className="space-y-4">
          <h1 className="text-lg font-semibold">
            {project.name} – {issueCode}
          </h1>
          <p className="text-sm text-slate-400">
            No se encontraron URLs con este tipo de issue en el último crawl.
          </p>
        </div>
      </AuthGuard>
    );
  }

  const firstDetails: IssueDetailsPayload = JSON.parse(issues[0].details || "{}");

  return (
    <AuthGuard>
      <div className="space-y-5">
        <div className="flex flex-wrap justify-between gap-2 items-center">
          <div>
            <h1 className="text-lg font-semibold">
              {project.name} – {firstDetails.issue_name || issueCode}
            </h1>
            <p className="text-xs text-slate-400">
              {project.domain} · Issue code:{" "}
              <span className="font-mono">{issueCode}</span>
            </p>
          </div>
          <div className="flex gap-2 items-center">
            <CategoryPill category={firstDetails.category} />
            <SeverityPill severity={firstDetails.severity} />
          </div>
        </div>

        <Card>
          <div className="space-y-2">
            <h2 className="text-sm font-semibold">Cómo leer este reporte</h2>
            <p className="text-xs text-slate-400">
              Cada fila representa una URL afectada por este issue.
            </p>
            <ul className="list-disc pl-4 text-xs text-slate-400 space-y-1">
              <li>URL y código de respuesta HTTP.</li>
              <li>Métricas clave de rendimiento cuando aplica (LCP, CLS, TBT, score).</li>
              <li>Explicación del problema e instrucción concreta para el implementador.</li>
              <li>Casilla “Implementado” para marcar cuando el ajuste se aplique.</li>
            </ul>
          </div>
        </Card>

        <IssueTable issues={issues} />
      </div>
    </AuthGuard>
  );
}
