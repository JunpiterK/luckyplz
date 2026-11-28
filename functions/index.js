import locales from "../scripts/og-assets/home-share-locales.json";

const countryLanguages = new Map(
  Object.entries(locales).flatMap(([code, entry]) => entry.countries.map(country => [country, code]))
);

function languageCode(value) {
  const tag = (value || "").trim().toLowerCase().replace(/_/g, "-");
  if (!/^[a-z]{2,3}(?:-[a-z0-9]{1,8})*$/.test(tag)) return null;
  if (/^en-(gb|uk)(-|$)/.test(tag)) return "gb";
  const primary = tag.split("-")[0];
  return Object.hasOwn(locales, primary) ? primary : null;
}

function shareLanguage(request) {
  const explicit = languageCode(new URL(request.url).searchParams.get("lang"));
  if (explicit) return explicit;

  const accepted = request.headers.get("Accept-Language") || "";
  let preferred = null;
  let bestQuality = 0;
  const excluded = new Set();
  for (const range of accepted.split(",")) {
    const match = range.trim().match(/^([\w*-]+)(?:\s*;\s*q\s*=\s*(0(?:\.\d{0,3})?|1(?:\.0{0,3})?))?$/i);
    if (!match) continue;
    const code = languageCode(match[1]);
    const quality = match[2] === undefined ? 1 : Number(match[2]);
    if (code && quality === 0) excluded.add(code);
    if (code && quality > bestQuality) {
      preferred = code;
      bestQuality = quality;
    }
  }
  if (preferred) return preferred;

  const agent = request.headers.get("User-Agent") || "";
  if (/kakaotalk|kakaostory|kakaoscrap|kakaobot/i.test(agent)) return excluded.has("ko") ? "en" : "ko";
  // A preview server's IP identifies its data centre rather than the person sharing.
  if (request.cf?.botManagement?.verifiedBot ||
      /bot\b|crawler|spider|facebookexternalhit|meta-external|whatsapp|\bline(?:[-/ ]|$)|preview|unfurl/i.test(agent)) return "en";
  const countryLanguage = countryLanguages.get(request.cf?.country);
  return countryLanguage && !excluded.has(countryLanguage) ? countryLanguage : "en";
}

export async function onRequest({ request, env, next }) {
  if (request.method !== "GET" && request.method !== "HEAD") return next();
  const code = shareLanguage(request);
  const entry = locales[code];
  // Fetch the unconditioned asset: its ETag is the same for every language.
  const source = await env.ASSETS.fetch(new Request(new URL("/", request.url), {method: request.method}));
  if (source.status !== 200 || !source.headers.get("Content-Type")?.includes("text/html")) return source;
  const response = new Response(source.body, source);
  response.headers.set("Cache-Control", "private, no-store, max-age=0");
  response.headers.append("Vary", "Accept-Language, User-Agent, CF-IPCountry");
  for (const header of ["ETag", "Last-Modified", "Content-Length", "Accept-Ranges"]) response.headers.delete(header);
  if (request.method === "HEAD") return response;

  const values = {
    "og:title": entry.title, "twitter:title": entry.title,
    "og:image:alt": entry.alt, "twitter:image:alt": entry.alt,
    "og:locale": entry.locale,
    "og:url": "https://luckyplz.com" + (entry.path || "/?lang=" + code),
  };
  return new HTMLRewriter()
    .on("html", {element(el) { el.setAttribute("data-share-locale", code); }})
    .on("head meta", {element(el) {
      const key = el.getAttribute("property") || el.getAttribute("name");
      if (Object.hasOwn(values, key)) el.setAttribute("content", values[key]);
    }})
    .transform(response);
}
