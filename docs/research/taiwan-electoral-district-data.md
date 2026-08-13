# Research: Taiwan electoral district data, population data, and legal rules for redistricting

Date: 2026-08-13
Purpose: Inform the product spec for 自己的選區自己畫 (draw-your-own legislative electoral district tool). Factual research only, not legal advice. Uncertain/unverified claims are flagged explicitly.

## 1. 行政區界線資料 (administrative boundary data)

- **Provider**: All authoritative boundary data (縣市 / 鄉鎮市區 / 村里) traces back to 內政部國土測繪中心 (National Land Surveying and Mapping Center, NLSC), republished via 政府資料開放平台 (data.gov.tw).
- **村里界圖 (village/li boundaries)**:
  - TWD97 lat/long version: https://data.gov.tw/dataset/7438
  - TWD97 119°E TM2 zone version: https://data.gov.tw/dataset/7439
  - Format: **Shapefile (SHP) only** on data.gov.tw — no native GeoJSON.
  - License: **政府資料開放授權條款 (Government Open Data License) v1** — free to use, broadly equivalent to CC BY, attribution required per license text.
  - Update frequency: **不定期更新 (irregular)** — no fixed cadence. First published 2014-03-04.
  - Providing agency: 內政部國土測繪中心; contact listed as Wu Jia-Long, 04-22522966 ext. 340.
- **鄉鎮市區界線 (township/district boundaries)**: https://data.gov.tw/dataset/7441 (same agency/license/format pattern).
- **直轄市、縣市界線 (county/municipality boundaries)**: https://data.gov.tw/dataset/7442.
- **Other official portals**:
  - TGOS 地理資訊圖資雲服務平台 (https://www.tgos.tw / https://map.tgos.tw) — metadata/catalog and viewer; acts more as a discovery layer pointing back to NLSC-origin data than a distinct source.
  - 國土測繪圖資服務雲 "下載專區" (https://maps.nlsc.gov.tw/MbIndex_qryPage.action?fun=8) — NLSC's own download portal; likely has WMS/WFS services in addition to file downloads (not independently confirmed which specific layers expose WMS/WFS — **flagged as unverified**, worth checking directly before relying on a live API).
  - 國土測繪圖資e商城 (https://whgis-nlsc.moi.gov.tw/GisMap/NLSCGisMap.aspx) — another NLSC storefront, may carry additional/derivative products.
- **Community-converted GeoJSON/TopoJSON** (since gov data ships as SHP only):
  - `g0v/twgeojson` — https://github.com/g0v/twgeojson — covers 縣市/鄉鎮區/村里 **and legislative districts (選區)** as geojson/topojson, simplified with d3.simplify, derived from MOI township data.
  - `dkaoster/taiwan-atlas` — https://github.com/dkaoster/taiwan-atlas — pre-built TopoJSON from MOI data, MIT licensed.
  - `ronnywang/twgeojson` — https://github.com/ronnywang/twgeojson — another administrative-boundary GeoJSON conversion.
  - Practical implication for the spec: the project will very likely need to **convert SHP → GeoJSON/TopoJSON itself** (or reuse one of the above community conversions) rather than pull GeoJSON directly from an official government API.

## 2. 人口統計資料 (population data)

- **Source**: 內政部戶政司 (Department of Household Registration, https://www.ris.gov.tw), republished on data.gov.tw.
- Key datasets found:
  - 各村（里）戶籍人口統計月報表 (monthly village-level household-registered population report): https://data.gov.tw/dataset/8411
  - 各村（里）戶籍人口統計月報表（新增區域代碼） (same, with added region codes): https://data.gov.tw/dataset/77140
  - 村里戶數、單一年齡人口（新增區域代碼） (village household counts + single-age population breakdown): https://data.gov.tw/dataset/77132
- **Granularity**: 村里 (village) level, nationwide.
- **Update frequency**: **monthly** ("月報表").
- **API**: ris.gov.tw exposes an open-data API — docs at https://www.ris.gov.tw/rs-opendata/api/Main/docs/v1 — so population figures can likely be pulled programmatically rather than only as bulk file downloads (format of API responses, e.g. JSON, was not independently confirmed — **flagged as unverified**, check the docs page directly).
- ris.gov.tw also has a dedicated portal section "人口統計資料庫導覽" (https://www.ris.gov.tw/app/portal/674) and "人口統計資料" (https://www.ris.gov.tw/app/portal/346) for browsing available tables.
- For redistricting specifically, Article 37 of 公職人員選舉罷免法 (see §4 below) says the CEC uses the **戶籍統計之人口數 (household-registered population count) as of month-end, 28 months before the sitting term ends** as the official population basis — so the product may want to let users pick/compare a specific historical monthly snapshot rather than "latest" population, to mirror how official redistricting actually works.

## 3. 現行選區劃分資料 (current electoral district boundaries as machine-readable data)

- 中央選舉委員會 (CEC) runs an open-data portal: **https://data.cec.gov.tw/** — confirmed to list a dataset titled **「第11屆立法委員選舉區範圍」** (11th Legislative Yuan electoral district boundaries).
  - Could not confirm the exact file format(s) (SHP/GeoJSON/KML) or license from the catalog listing alone — **flagged as unverified, needs a direct visit to the dataset page** to check "格式" and "授權方式" fields before committing to it as a data source.
- data.gov.tw also mirrors a CEC "選舉資料庫（含選舉區資料）" dataset: https://data.gov.tw/dataset/13119 — again, exact electoral-district-geometry format not confirmed from search alone.
- CEC also runs **db.cec.gov.tw** (選舉資料庫, https://db.cec.gov.tw/ and https://db.cec.gov.tw/Visual) — election results database, and **web.cec.gov.tw** for official announcements (PDF maps of each 選舉區劃分簡圖, e.g. https://web.cec.gov.tw/central/article/15955 for the 7th Legislative Yuan).
- **Community derivative**: `g0v/twgeojson` (above) already packages current legislative district (選區) boundaries as GeoJSON/TopoJSON — likely the fastest path to a working current-boundaries layer, pending a license/currency check (need to confirm it's been updated for the districts effective since the last redistricting cycle).
- **Net assessment**: CEC does appear to publish current 立委 district boundaries as data (not only PDF maps) via data.cec.gov.tw, but the concrete format/license needs direct confirmation — this is the single most important gap to close before scoping the "load current districts as a baseline layer" feature.

## 4. 法定劃分規則 (legal rules for legislative district boundaries)

**公職人員選舉罷免法 (Public Officials Election and Recall Act), Article 37** — full text of the operative paragraphs (fetched from 全國法規資料庫, law.moj.gov.tw, pcode=D0020010):

- **§37 ¶1**: 立法委員選舉區... 由中央選舉委員會劃分... 並應於發布選舉公告時公告。但選舉區有變更時，應於公職人員任期或規定之日期屆滿一年前發布之。
  (CEC delimits legislative districts; districts are announced with the election announcement; if districts are *changed*, the change must be announced at least 1 year before the relevant term ends.)
- **§37 ¶2**: 前項選舉區，應斟酌**行政區域、人口分布、地理環境、交通狀況、歷史淵源**及應選出名額劃分之。
  (Districts must be delimited having regard to administrative boundaries, population distribution, geography, transport conditions, historical origin, and number of seats.)
- **§37 ¶3**: For changing an existing legislative district: CEC uses the household-registered population count **as of the end of the month, 28 months (2 years 2 months) before the current term ends**, and must submit the change proposal to the Legislative Yuan for approval **20 months (1 year 8 months)** before term end. The Legislative Yuan votes on the proposal **by 直轄市/縣市 unit** (approve or reject each city/county's proposal as a whole); on rejection, CEC revises and resubmits within 30 days; final approval must complete 13 months before term end, with unresolved cases settled by negotiation between the Executive Yuan and Legislative Yuan presidents.

**Important finding — the ±15% deviation rule and the "don't split townships" rule are NOT in the statute text itself.** I checked both Article 37 of the Act (full text above) and 公職人員選舉罷免法施行細則 (its enforcement rules, via law.cec.gov.tw) — neither contains an explicit population-deviation percentage or an explicit no-township-splitting clause. The statute only gives the vague §37 ¶2 factor list ("行政區域、人口分布、地理環境、交通狀況、歷史淵源").

The specific numeric rule commonly cited (and consistent with what the user expected) — sourced from a 立法院 (Legislative Yuan) research report on legislative district delimitation (https://www.ly.gov.tw/Pages/Detail.aspx?nodeid=6590&pid=85436, and companion report at nodeid=6586&pid=83486) — describes these as the **CEC's operational delimitation principles** (i.e., how CEC interprets/operationalizes §37 ¶2 in practice), not codified statutory text:

- 每一選舉區人口數與該直轄市、縣市應選名額除人口數之平均數，相差以**不超過15%為原則** (each district's population should not deviate from the average — total population ÷ seats for that city/county — by more than 15%, as a general principle).
- 單一鄉鎮市區人口數達平均數以上者，應劃為一個選舉區；其人口數超過平均數15%以上時，得將超過部分的村里與相鄰鄉鎮市區合併劃為一個選舉區 (a single township/district whose population meets/exceeds the average becomes one district; if it exceeds the average by more than 15%, the excess population's villages can be split off and combined with an adjacent township/district).
- 人口未達平均數之鄉鎮市區，應與相鄰鄉鎮市區合併劃為一個選舉區 (townships below the average must be merged with adjacent townships).
- 村里本身原則上不得分割；必要時才能將同一鄉鎮市區內的村里拆分去合併鄰近選舉區，且不得劃入不相鄰地區 (villages themselves generally cannot be split; only when necessary can villages within the same township be reassigned to a neighboring district, and non-contiguous areas cannot be combined into one district).

**Caveat / uncertainty to flag explicitly in the spec**: I was not able to independently trace the "15%" figure to a specific numbered CEC 公告 (announcement) or a specific clause of a named administrative rule — the Legislative Yuan report describes it as the principle CEC has applied, but treat the exact "15%" number and the "single village cannot be split" rule as **CEC administrative practice/guideline, not hard statutory law**, until confirmed directly against a CEC-published 劃分原則 document for a specific redistricting cycle (e.g. the most recent one effective for the 11th or upcoming 12th Legislative Yuan election). This distinction matters for the product: encoding "±15%" as a hard validation rule in the UI is defensible as reflecting long-standing CEC practice, but should probably be labeled as "CEC's stated principle" rather than "the law requires."

**Update (2026-08-13 follow-up research, resolving open question #4 below): the source document has now been identified and named**, via a peer-reviewed academic citation rather than a directly-hosted CEC web page (see "what was and wasn't found" below for the search trail):

- **Document title**: 《第7屆立法委員直轄市縣市選舉區劃分原則》("Principles for Delimiting Legislative Districts by Municipality/County for the 7th Legislative Yuan"), adopted by **中央選舉委員會第349次委員會議** (CEC's 349th committee meeting) in **August 2005 (民國94年8月)**, in the run-up to the 7th Legislative Yuan election (2008) — this was CEC's first delimitation exercise after the constitutional amendment that introduced single-member districts.
- **Source for this citation**: 王保鍵 (Wang Pao-Chien), 〈選舉制度與族群政治：以新竹縣立法委員選區劃分為例〉("The Electoral System and Ethnic Politics: The Case of Legislative Redistricting in Hsinchu County"), *選舉研究 (Journal of Electoral Studies)*, Vol. 27 No. 2 (Nov 2020), pp. 1–48, DOI: 10.6612/tjes.202011_27(2).0001 — a peer-reviewed article in Taiwan's leading electoral-studies journal. Footnote 32 quotes the operative text verbatim:

  > 「依中央選舉委員會第349次會議通過《第7屆立法委員直轄市縣市選舉區劃分原則》規定：每一選舉區人口數與各該直轄市、縣（市）應選名額除人口數之平均數，相差以不超過15%為原則；單一鄉（鎮、市、區）其人口數達該直轄市、縣（市）應選名額除人口數之平均數以上者，應劃為一個選舉區；其人口數如超過平均數15%以上時，得將人口超過之部分村、里與相鄰接之鄉（鎮、市、區）劃為一個選舉區。」

  This matches — and directly confirms — the 15% rule and the village-splitting-only-when-necessary rule already summarized above from the 立法院 report. The same footnote gives a concrete illustration of the village-splitting mechanic in practice: for the 7th LY, 台北市（士林區、松山區、中正區）、新北市（原三重市、新莊市、板橋市、中和市）、桃園市（原中壢市）、臺中市（原大里市）、高雄市（三民區） all had their township/district boundaries split down to the **里 (village)** level specifically to satisfy the ±15% rule. The paper also notes CEC additionally formed a "立法委員選舉區劃分專案小組" (legislative district delimitation task force) and referenced a companion document, 《劃分第七屆立法委員直轄市縣市選舉區劃分準繩》 ("Criteria for Delimiting the 7th LY Municipality/County Electoral Districts"), to operationalize the principles — that companion document's text was not independently located in this pass either.

- **Important further finding — this principle document was NOT reissued for the most recent actual redistricting cycle.** The same paper states explicitly (main text and footnote 56): for the **10th Legislative Yuan** redistricting (finalized 2019, effective for the 2020 election, and still the boundary set in force for the 11th LY / 2024 election, since no further change was triggered), **CEC did not adopt a new or updated 劃分原則 document** ("第10屆立法委員選區劃分，中央選舉委員會則不再訂定相關劃分原則或準繩")。The practical consequence: several of the district changes CEC actually sent to the Legislative Yuan for the 10th LY cycle (Taichung, Kaohsiung) had population deviations **exceeding 20%** from the district average — i.e., *double* the "±15%" figure in the 2005 document — with CEC's stated justification being "行政區域完整性" (administrative-boundary integrity) taking priority over the population-deviation target in those specific cases. New Hsinchu County's 2019 district split (the case study of the paper) also exceeded 15% (17.91%/-17.91%) but stayed under 20%.
  - **Practical implication for this product**: the "±15%" figure should be treated as **CEC's originally-adopted 2005 operating principle for the 7th LY cycle, carried forward informally as a norm rather than as a document CEC has continued to formally re-adopt or strictly enforce at each 10-year review** — the most recent actual redistricting (10th LY, governing today's 11th LY districts) shows CEC treating it as a soft target that can be overridden by "administrative boundary completeness," not a hard cap. The product should probably surface both the ±15% figure *and* this caveat (i.e., don't hard-block a user's proposed map at 15% deviation — CEC's own most recent practice tolerates 17–20%+ in specific cases).

**What was checked and NOT found in this pass** (so the gap is visible rather than silently dropped): a directly-hosted, primary-source copy of 《第7屆立法委員直轄市縣市選舉區劃分原則》 itself (or its companion 準繩 document) could not be located as a standalone published file. Checked and came up empty: (a) web.cec.gov.tw search/article listings, (b) data.cec.gov.tw, (c) law.cec.gov.tw's LawQuery.aspx regulation search (the document does not appear in CEC's own 法規 database — consistent with it being an internal committee-meeting resolution rather than a formally promulgated 法規 or numbered 公告), (d) gazette.nat.gov.tw (Executive Yuan Gazette) searches for CEC announcements/orders around 2005 and 2018 (fetched and read two candidate PDFs directly — a 2018-04-30 CEC order turned out to be about poll-watcher recruitment rules, unrelated; a 2015-11-13 CEC announcement was the 9th LY district/seat list itself, with no stated principles text), (e) 立法院公報 (Legislative Yuan Gazette) — a 2005-05-25 committee session that a search snippet suggested might discuss this turned out, on full read, to be an unrelated debate about absentee-voting legislation. If a future pass wants the primary CEC document itself rather than the academic citation, the next things to try would be: a public records/FOI-style request to CEC's 法政處 (Legal & Planning Division, which reportedly owns this material per the paper's institutional description), or CEC's public hearing materials for the 10th LY cycle (公聽會, ~2018-05-14) which are known to exist per web.cec.gov.tw article listings (e.g. https://web.cec.gov.tw/central/article/45169) but whose full content could not be extracted via automated fetch in this pass (JS-rendered page).

Constitutional/statutory context also worth noting for scoping: regional (區域) legislator seats are allocated across counties/cities by population proportion with a constitutional floor of 1 seat per county/city (this determines *how many* districts a county/city gets before districts are drawn within it) — small jurisdictions (金門、連江、澎湖、宜蘭、花蓮、台東、基隆、新竹市、嘉義市 per one source) get only 1 seat, meaning the whole county/city *is* the district (per Article 35, referenced but not independently re-verified against the statute text in this pass — **flagged as needing direct §35 confirmation** if the spec depends on exact seat-allocation logic).

## 5. Existing open-source / civic-tech projects to learn from

- **`g0v/twgeojson`** (https://github.com/g0v/twgeojson) — most directly relevant: already ships Taiwan's counties/townships/villages **and legislative districts** as GeoJSON/TopoJSON, derived from MOI data, simplified for web visualization. Good candidate as a base-map/current-districts data source, or at least as a reference implementation for the SHP→web-geometry pipeline.
- **`dkaoster/taiwan-atlas`** (https://github.com/dkaoster/taiwan-atlas) — MIT-licensed pre-built TopoJSON from MOI data; simpler/more actively maintained alternative to twgeojson for base boundaries (does not appear to include electoral districts specifically, only administrative boundaries — **not fully verified**).
- **`ronnywang/twgeojson`** (https://github.com/ronnywang/twgeojson) — another independent conversion of administrative boundaries to GeoJSON.
- **db.cec.gov.tw / db.cec.gov.tw/Visual** — CEC's own election results database and visualization; not a drawing tool, but the canonical source for "what were the results in this district" if the product wants to overlay past results on proposed districts.
- **No dedicated Taiwan redistricting-drawing/simulation tool was found.** Searches for g0v hackathon material specifically from hackath13n's "自己的選區自己畫" proposal (the one referenced in this repo's README) did not surface an archived hackfoldr/HackMD page or any resulting code repo in this pass — **the original proposal's pad/repo could not be located and may need to be found via the g0v hackathon's own archive (jothon.g0v.tw/events/) or by contacting people who attended hackath13n**, since the README explicitly says this repo intends to build something "略有不同" (somewhat different) from that original pitch.
- **International analogs worth studying** (not Taiwan-specific, but directly relevant as prior art for "citizen-drawn redistricting" UX/algorithms):
  - **DistrictBuilder** (https://www.districtbuilder.org/) — open-source, purpose-built public redistricting tool (US-focused) — closest existing analog to what this project wants to build.
  - **ALARM Project** (https://alarm-redist.org/japan/) — algorithmic redistricting simulation for Japan's House of Representatives single-member districts, open source, methodologically close (similar "single-member district + population-deviation constraint" system to Taiwan's).
  - Redistricting Data Hub's tool survey (https://redistrictingdatahub.org/tools/choose-your-own-mapping-tool/) — a broader catalog of US redistricting mapping tools, useful for feature/UX comparison even though US-specific.
- 台灣公民科技資料庫 (Civic Tech Taiwan, https://civictech.tw/) is worth a direct search/browse (not done in this pass) as the most likely place a prior g0v redistricting attempt, if any exists beyond the hackath13n pitch, would be indexed.

## Summary of open questions / follow-ups before finalizing the spec

1. Confirm exact file format(s) and license on the **data.cec.gov.tw** "第11屆立法委員選舉區範圍" dataset directly (topic 3) — this determines whether current-district boundaries can be loaded without a conversion step.
2. Confirm whether NLSC's 國土測繪圖資服務雲 exposes a live **WMS/WFS** endpoint for 村里/鄉鎮市區 boundaries, vs. file-download-only (topic 1).
3. Confirm the ris.gov.tw open-data API's response format and whether it supports village-level population queries directly (topic 2).
4. ~~Trace the **±15% population deviation rule** and the **village-non-splitting rule** to a specific CEC-published 劃分原則/公告 document for a specific redistricting cycle, rather than relying solely on the Legislative Yuan's summary report~~ **RESOLVED (2026-08-13 follow-up pass) — see topic 4 above.** The rule traces to a named CEC document, 《第7屆立法委員直轄市縣市選舉區劃分原則》 (adopted via CEC's 349th committee meeting, Aug 2005), confirmed via a peer-reviewed academic citation (王保鍵 2020, *選舉研究* 27(2)) rather than a directly-hosted primary-source CEC page (none could be found — see topic 4 for the full search trail of what was checked). Important nuance discovered: CEC did **not** re-adopt or update this principles document for the most recent actual redistricting (10th LY, 2019/2020, still governing today's 11th LY districts) — several districts in that cycle exceeded even 20% deviation, meaning "±15%" is best described in the spec as CEC's original 2005 principle, informally carried forward, not a rule CEC has continued to strictly apply or formally re-issue.
5. Locate the original g0v hackath13n "自己的選區自己畫" proposal pad/repo, if it still exists, to understand what was scoped and avoid duplicating groundwork (topic 5).
