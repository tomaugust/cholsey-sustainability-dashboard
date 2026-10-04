import type { APIRoute } from "astro";
import { getTiles } from "../lib/data";

// Hand-rolled sitemap (the Astro 4-compatible integration was not worth a dependency).
export const GET: APIRoute = ({ site }) => {
  const base = new URL(
    import.meta.env.BASE_URL.replace(/\/?$/, "/"),
    site,
  ).toString();
  const paths = [
    "",
    ...getTiles().map((t) => `metrics/${t.id}/`),
    "compare/",
    "methodology/",
    "glossary/",
    "about/",
  ];
  const body = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${paths.map((p) => `  <url><loc>${base}${p}</loc></url>`).join("\n")}
</urlset>
`;
  return new Response(body, { headers: { "Content-Type": "application/xml" } });
};
