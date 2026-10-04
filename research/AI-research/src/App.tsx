import { useMemo, useRef, useState } from 'react';
import {
  ArrowDownToLine,
  ArrowUpRight,
  BookOpenText,
  Check,
  CheckCheck,
  ChevronDown,
  Clipboard,
  FilePlus2,
  FileText,
  Globe2,
  Layers2,
  LoaderCircle,
  Plus,
  Search,
  Sparkles,
  X,
} from 'lucide-react';

type Source = {
  id: string;
  title: string;
  url: string;
  domain: string;
  snippet: string;
  content?: string;
  kind: 'web' | 'document';
};

type Tab = 'overview' | 'compare' | 'report';

const sampleSources: Source[] = [
  {
    id: 'unesco',
    title: 'Guidance for generative AI in education and research',
    url: 'https://www.unesco.org/en/articles/guidance-generative-ai-education-and-research',
    domain: 'unesco.org',
    snippet: 'UNESCO guidance calls for a human-centred approach to generative AI in education, with attention to privacy, age limits, equity, and pedagogical validation.',
    kind: 'web',
  },
  {
    id: 'ed-gov',
    title: 'Artificial Intelligence and the Future of Teaching and Learning',
    url: 'https://tech.ed.gov/ai-future-of-teaching-and-learning/',
    domain: 'tech.ed.gov',
    snippet: 'The U.S. Department of Education report recommends keeping humans in the loop and using AI to augment, rather than replace, the work of educators.',
    kind: 'web',
  },
  {
    id: 'oecd',
    title: 'Digital Education Outlook 2023',
    url: 'https://www.oecd.org/education/digital-education-outlook-2023/',
    domain: 'oecd.org',
    snippet: 'OECD examines how digital technologies can support teaching and learning, and highlights the importance of evidence, teacher capacity, and responsible implementation.',
    kind: 'web',
  },
];

const suggestions = [
  'How should schools evaluate generative AI tutors?',
  'What interventions reduce urban heat exposure?',
  'Recent evidence on heat pumps and household costs',
];

function sentenceFor(source: Source, query: string): string {
  const text = source.content || source.snippet;
  const sentences = text.match(/[^.!?]+[.!?]+|[^.!?]+$/g) ?? [text];
  const terms = query.toLowerCase().split(/[^a-z0-9]+/).filter((term) => term.length > 3);
  const ranked = sentences
    .map((sentence, index) => ({
      sentence: sentence.trim(),
      index,
      score: terms.reduce((score, term) => score + (sentence.toLowerCase().includes(term) ? 1 : 0), 0),
    }))
    .sort((a, b) => b.score - a.score || a.index - b.index);
  if (ranked[0]?.score) return ranked[0].sentence;
  return text.length > 360 ? `${text.slice(0, 357).trimEnd()}...` : text;
}

function App() {
  const [query, setQuery] = useState('How should schools evaluate generative AI tutors?');
  const [sources, setSources] = useState<Source[]>(sampleSources);
  const [selectedIds, setSelectedIds] = useState<string[]>(sampleSources.map((source) => source.id));
  const [tab, setTab] = useState<Tab>('overview');
  const [isSearching, setIsSearching] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [notice, setNotice] = useState('Sample investigation · replace with live search');
  const [report, setReport] = useState('');
  const [searchError, setSearchError] = useState('');
  const fileInput = useRef<HTMLInputElement>(null);

  const selectedSources = useMemo(
    () => sources.filter((source) => selectedIds.includes(source.id)),
    [sources, selectedIds],
  );
  const evidence = useMemo(
    () => selectedSources.map((source) => ({ source, takeaway: sentenceFor(source, query) })),
    [selectedSources, query],
  );

  async function searchWeb(nextQuery = query) {
    const trimmed = nextQuery.trim();
    if (trimmed.length < 3) {
      setSearchError('Add a little more detail to your research question.');
      return;
    }
    setQuery(trimmed);
    setSearchError('');
    setIsSearching(true);
    setNotice('Searching the web…');
    try {
      const response = await fetch('/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: trimmed, max_results: 8 }),
      });
      if (!response.ok) throw new Error('The research API is not available.');
      const data: { results: Array<{ title: string; url: string; snippet: string; domain: string }> } = await response.json();
      const found = data.results.map((result, index) => ({ ...result, id: `web-${Date.now()}-${index}`, kind: 'web' as const }));
      setSources((current) => [...found, ...current.filter((source) => source.kind === 'document')]);
      setSelectedIds(found.map((source) => source.id));
      setNotice(`${found.length} web sources · live search`);
      if (!found.length) setSearchError('No sources came back for that question. Try a broader search.');
    } catch {
      setNotice('Search is offline · showing the sample investigation');
      setSearchError('Start the API to run live web search. Your sample sources are still available.');
    } finally {
      setIsSearching(false);
    }
  }

  function toggleSource(id: string) {
    setSelectedIds((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]);
  }

  async function importDocuments(files: FileList | null) {
    if (!files) return;
    const accepted: Source[] = [];
    for (const file of Array.from(files)) {
      if (!/\.(txt|md|csv|json)$/i.test(file.name)) continue;
      if (file.size > 1_000_000) {
        setSearchError(`${file.name} is over the 1 MB text-file limit.`);
        continue;
      }
      const content = await file.text();
      accepted.push({
        id: `doc-${Date.now()}-${accepted.length}`,
        title: file.name,
        url: `local://${encodeURIComponent(file.name)}`,
        domain: 'Local document',
        snippet: content.slice(0, 360),
        content,
        kind: 'document',
      });
    }
    if (accepted.length) {
      setSources((current) => [...accepted, ...current]);
      setSelectedIds((current) => [...accepted.map((source) => source.id), ...current]);
      setNotice(`${accepted.length} local document${accepted.length === 1 ? '' : 's'} added`);
      setSearchError('');
    }
  }

  async function extractSelected() {
    const targets = selectedSources.filter((source) => source.kind === 'web' && !source.content);
    if (!targets.length) {
      setNotice('Selected sources already have readable text');
      return;
    }
    setIsExtracting(true);
    let count = 0;
    for (const source of targets) {
      try {
        const response = await fetch('/api/extract', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url: source.url }),
        });
        if (!response.ok) continue;
        const data: { content: string } = await response.json();
        setSources((current) => current.map((item) => item.id === source.id ? { ...item, content: data.content } : item));
        count += 1;
      } catch {
        // Keep the search result snippet when a publisher blocks extraction.
      }
    }
    setIsExtracting(false);
    setNotice(`Extracted full text from ${count} of ${targets.length} sources`);
  }

  function makeReport() {
    const references = evidence.map(({ source }, index) => `[${index + 1}] ${source.title}. ${source.domain}. ${source.url}`).join('\n');
    const findings = evidence.map(({ takeaway }, index) => `${index + 1}. ${takeaway} [${index + 1}]`).join('\n\n');
    const summary = evidence.length
      ? `This brief contains ${evidence.length} source-anchored finding${evidence.length === 1 ? '' : 's'} related to the research question. Search-result excerpts are preliminary; extract full text and review the original context before treating them as conclusions.`
      : 'Select at least one source to synthesize findings.';
    const draft = `# Research brief\n\n## Question\n${query}\n\n## Summary\n${summary}\n\n## Findings\n${findings || 'No evidence selected.'}\n\n## Source comparison\n${evidence.map(({ source }, index) => `- [${index + 1}] ${source.domain}: ${source.kind === 'document' ? 'Imported document' : 'Web source'}; ${source.content ? 'full text extracted' : 'search-result excerpt only'}.`).join('\n')}\n\n## References\n${references || 'No references yet.'}\n`;
    setReport(draft);
    setTab('report');
    setNotice('Draft report generated from selected evidence');
  }

  async function copyReport() {
    try {
      await navigator.clipboard.writeText(report);
      setNotice('Report copied to clipboard');
    } catch {
      setNotice('Clipboard access is unavailable in this browser');
    }
  }

  function downloadReport() {
    const blob = new Blob([report], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = 'fieldnote-research-brief.md';
    anchor.click();
    URL.revokeObjectURL(url);
    setNotice('Markdown report downloaded');
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="Fieldnote research desk">
          <span className="brand-mark"><BookOpenText size={18} strokeWidth={1.8} /></span>
          <span>fieldnote<span className="brand-period">.</span></span>
          <span className="brand-divider" />
          <span className="brand-product">RESEARCH DESK</span>
        </a>
        <div className="topbar-right">
          <span className="workspace-label"><span className="status-dot" /> Personal workspace</span>
          <button className="icon-button top-add" aria-label="New investigation" title="New investigation" onClick={() => { setQuery(''); setSources([]); setSelectedIds([]); setReport(''); setNotice('New investigation'); }}><Plus size={17} /></button>
          <span className="avatar" title="Researcher">R</span>
        </div>
      </header>

      <div className="workspace" id="top">
        <aside className="sidebar">
          <div className="sidebar-label">YOUR DESK</div>
          <button className="sidebar-link active"><Layers2 size={16} /><span>Research canvas</span><span className="sidebar-count">{sources.length}</span></button>
          <button className="sidebar-link" onClick={() => fileInput.current?.click()}><FilePlus2 size={16} /><span>Import documents</span></button>
          <div className="sidebar-section-heading"><span>RECENT INVESTIGATIONS</span><ChevronDown size={13} /></div>
          <button className="recent-item selected"><span className="recent-bullet" /><span className="recent-text">AI tutors in schools</span></button>
          <button className="recent-item" onClick={() => { setQuery(suggestions[1]); }}><span className="recent-bullet muted" /><span className="recent-text">Urban heat strategies</span></button>
          <button className="recent-item" onClick={() => { setQuery(suggestions[2]); }}><span className="recent-bullet muted" /><span className="recent-text">Heat pump evidence</span></button>
          <div className="sidebar-bottom">
            <div className="storage-line"><span>SESSION SOURCES</span><span>{sources.length} / 20</span></div>
            <div className="storage-track"><span style={{ width: `${Math.min(sources.length / 20 * 100, 100)}%` }} /></div>
            <div className="privacy-note"><span className="privacy-icon"><Check size={12} /></span> Documents stay in this session</div>
          </div>
        </aside>

        <main className="main-panel">
          <div className="page-heading">
            <div>
              <div className="eyebrow"><span className="eyebrow-line" /> INVESTIGATION  /  04 OCT 2026</div>
              <h1>Research canvas</h1>
            </div>
            <div className="heading-meta"><span className="live-indicator" /> {notice}</div>
          </div>

          <section className="search-panel" aria-label="Search the web">
            <div className="search-panel-top"><span className="search-kicker"><Globe2 size={14} /> RESEARCH QUESTION</span><span className="search-provider">WEB + YOUR DOCUMENTS</span></div>
            <div className="search-row">
              <Search className="search-leading" size={20} />
              <input value={query} onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter') void searchWeb(); }} placeholder="What are you investigating?" aria-label="Research question" />
              <button className="search-button" onClick={() => void searchWeb()} disabled={isSearching}>{isSearching ? <LoaderCircle className="spin" size={16} /> : <Search size={16} />}<span>{isSearching ? 'Searching' : 'Search sources'}</span></button>
            </div>
            {searchError && <div className="search-error"><span>{searchError}</span><button aria-label="Dismiss message" onClick={() => setSearchError('')}><X size={14} /></button></div>}
            {!sources.length && <div className="suggestions"><span>TRY</span>{suggestions.map((item) => <button key={item} onClick={() => { setQuery(item); void searchWeb(item); }}>{item}<ArrowUpRight size={12} /></button>)}</div>}
          </section>

          <div className="content-toolbar">
            <div className="tabs" role="tablist" aria-label="Research views">
              <button className={tab === 'overview' ? 'tab active' : 'tab'} onClick={() => setTab('overview')} role="tab" aria-selected={tab === 'overview'}>Overview <span>{selectedSources.length}</span></button>
              <button className={tab === 'compare' ? 'tab active' : 'tab'} onClick={() => setTab('compare')} role="tab" aria-selected={tab === 'compare'}>Compare <span>{selectedSources.length}</span></button>
              <button className={tab === 'report' ? 'tab active' : 'tab'} onClick={() => setTab('report')} role="tab" aria-selected={tab === 'report'}>Report</button>
            </div>
            <div className="toolbar-actions">
              <button className="text-action" onClick={() => fileInput.current?.click()}><FilePlus2 size={15} /> Add documents</button>
              <input ref={fileInput} type="file" accept=".txt,.md,.csv,.json,text/plain,text/markdown" multiple hidden onChange={(event) => { void importDocuments(event.target.files); event.target.value = ''; }} />
              <button className="text-action" onClick={() => void extractSelected()} disabled={isExtracting || !selectedSources.length}>{isExtracting ? <LoaderCircle className="spin" size={15} /> : <Sparkles size={15} />} Extract text</button>
              <button className="primary-small" onClick={makeReport} disabled={!selectedSources.length}><FileText size={14} /> Build report</button>
            </div>
          </div>

          {tab === 'overview' && <div className="overview-grid">
            <section className="evidence-column">
              <div className="section-heading"><div><h2>Evidence ledger</h2><p>Key passages from your selected sources</p></div><span className="count-pill">{selectedSources.length} SELECTED</span></div>
              {evidence.length ? <div className="evidence-list">{evidence.map(({ source, takeaway }, index) => <article className="evidence-item" key={source.id}>
                <div className="evidence-number">{String(index + 1).padStart(2, '0')}</div>
                <div className="evidence-body"><div className="source-meta"><span className={source.kind === 'document' ? 'source-type document' : 'source-type'}>{source.kind === 'document' ? <FileText size={11} /> : <Globe2 size={11} />}{source.kind === 'document' ? 'DOCUMENT' : source.domain}</span><span className="source-read-state">{source.content ? 'FULL TEXT' : 'SEARCH EXCERPT'}</span></div>
                  <h3>{source.title}</h3><p className="evidence-quote">{takeaway}</p>
                  <div className="evidence-footer"><a href={source.kind === 'web' ? source.url : undefined} target="_blank" rel="noreferrer" onClick={(event) => { if (source.kind === 'document') event.preventDefault(); }} className={source.kind === 'document' ? 'source-link local' : 'source-link'}>{source.kind === 'document' ? 'Local document' : source.domain}<ArrowUpRight size={12} /></a><button className="citation-chip" onClick={() => toggleSource(source.id)} title="Remove from synthesis">[{index + 1}] <Check size={11} /></button></div>
                </div>
              </article>)}</div> : <div className="empty-state"><BookOpenText size={24} /><h3>No evidence selected</h3><p>Search for sources or import a document to begin your investigation.</p></div>}
            </section>
            <aside className="right-column">
              <section className="synthesis-panel"><div className="panel-overline"><Sparkles size={14} /> EXTRACTIVE SYNTHESIS</div><h2>A first read</h2><p className="synthesis-copy">{selectedSources.length ? `The strongest excerpt-level matches for “${query}” from ${selectedSources.length} selected source${selectedSources.length === 1 ? '' : 's'}.` : 'Select sources to see an evidence-led synthesis of your research question.'}</p><div className="synthesis-rule" />{evidence.slice(0, 2).map(({ source, takeaway }, index) => <div className="synthesis-point" key={source.id}><span className="point-index">{String(index + 1).padStart(2, '0')}</span><p><strong>{source.domain}.</strong> {takeaway}</p></div>)}<div className="synthesis-footnote"><span className="footnote-mark">i</span> Excerpt-based draft · verify in the original source</div></section>
              <section className="source-stack"><div className="stack-heading"><div><h3>In this investigation</h3><span>{sources.length} SOURCES</span></div><button className="icon-button small" onClick={() => fileInput.current?.click()} aria-label="Add a document" title="Add a document"><Plus size={15} /></button></div>
                {sources.length ? <div className="source-stack-list">{sources.map((source) => <label className="source-row" key={source.id}><input type="checkbox" checked={selectedIds.includes(source.id)} onChange={() => toggleSource(source.id)} /><span className={`stack-icon ${source.kind}`} aria-hidden="true">{source.kind === 'document' ? <FileText size={14} /> : <Globe2 size={14} />}</span><span className="stack-source-text"><span className="stack-source-title">{source.title}</span><span className="stack-source-domain">{source.domain}</span></span></label>)}</div> : <p className="stack-empty">Sources you find will appear here.</p>}
                <button className="manage-sources" onClick={() => fileInput.current?.click()}><Plus size={14} /> Add a document</button>
              </section>
            </aside>
          </div>}

          {tab === 'compare' && <section className="compare-view"><div className="section-heading"><div><h2>Source comparison</h2><p>Read claims side by side; each excerpt links back to its source</p></div><span className="count-pill">{selectedSources.length} SOURCES</span></div>{selectedSources.length ? <div className="compare-grid">{evidence.map(({ source, takeaway }, index) => <article className="compare-card" key={source.id}><div className="compare-card-top"><span className="compare-index">SOURCE {String(index + 1).padStart(2, '0')}</span><button className="icon-button small" onClick={() => toggleSource(source.id)} aria-label="Remove source"><X size={14} /></button></div><h3>{source.title}</h3><span className="compare-domain">{source.domain}</span><blockquote>{takeaway}</blockquote><div className="compare-card-bottom"><span className="source-read-state">{source.content ? 'FULL TEXT EXTRACTED' : 'SEARCH EXCERPT ONLY'}</span>{source.kind === 'web' && <a href={source.url} target="_blank" rel="noreferrer" aria-label={`Open ${source.title}`}><ArrowUpRight size={15} /></a>}</div></article>)}</div> : <div className="empty-state"><Layers2 size={24} /><h3>Nothing to compare yet</h3><p>Select two or more sources from the source list.</p></div>}</section>}

          {tab === 'report' && <section className="report-view"><div className="section-heading"><div><h2>Research report</h2><p>Editable Markdown · citations stay linked to your source list</p></div><div className="report-actions"><button className="text-action" onClick={() => void copyReport()} disabled={!report}><Clipboard size={15} /> Copy</button><button className="primary-small" onClick={downloadReport} disabled={!report}><ArrowDownToLine size={15} /> Export .md</button></div></div>{report ? <div className="report-editor-wrap"><div className="report-paper-head"><span><FileText size={15} /> FIELDNOTE / RESEARCH BRIEF</span><span>{selectedSources.length} REFERENCES</span></div><textarea className="report-editor" value={report} onChange={(event) => setReport(event.target.value)} spellCheck={false} aria-label="Edit research report" /></div> : <div className="report-empty"><div className="report-empty-icon"><FileText size={22} /></div><h3>Your report starts with evidence</h3><p>Build a report to create a structured synthesis with numbered citations, a source comparison, and linked references.</p><button className="primary-small" onClick={makeReport} disabled={!selectedSources.length}><Sparkles size={14} /> Generate report</button></div>}</section>}

          <footer className="page-footer"><span><span className="footer-mark">F</span> FIELDNOTE RESEARCH DESK</span><span><CheckCheck size={13} /> Always verify extracted claims in their original context</span></footer>
        </main>
      </div>
    </div>
  );
}

export default App;
