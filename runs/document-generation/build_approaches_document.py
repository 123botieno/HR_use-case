"""Build a styled Word document using the standard OOXML package format."""
from pathlib import Path
from html import escape
from zipfile import ZipFile, ZIP_DEFLATED
from xml.etree import ElementTree as ET

OUT = Path("docs/Job_Matching_Approaches_LLM_BM25_TFIDF.docx")
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
parts = []

def p(text="", style=None, bold=False):
    props = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    runprops = "<w:rPr><w:b/></w:rPr>" if bold else ""
    parts.append(f'<w:p>{props}<w:r>{runprops}<w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>')

def title(text):
    p(text, "Heading1")

def sub(text):
    p(text, "Heading2")

def formula(text):
    p(text, "Formula")

def page():
    parts.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')

def table(headers, rows, widths=None):
    widths = widths or [int(10200 / len(headers))] * len(headers)
    xml = ['<w:tbl><w:tblPr><w:tblW w:w="0" w:type="auto"/><w:tblBorders>'
           '<w:top w:val="single" w:sz="4" w:color="D2DCE6"/>'
           '<w:left w:val="single" w:sz="4" w:color="D2DCE6"/>'
           '<w:bottom w:val="single" w:sz="4" w:color="D2DCE6"/>'
           '<w:right w:val="single" w:sz="4" w:color="D2DCE6"/>'
           '<w:insideH w:val="single" w:sz="4" w:color="D2DCE6"/>'
           '<w:insideV w:val="single" w:sz="4" w:color="D2DCE6"/>'
           '</w:tblBorders><w:tblCellMar><w:top w:w="90" w:type="dxa"/>'
           '<w:left w:w="100" w:type="dxa"/><w:bottom w:w="90" w:type="dxa"/>'
           '<w:right w:w="100" w:type="dxa"/></w:tblCellMar></w:tblPr><w:tblGrid>']
    xml.extend(f'<w:gridCol w:w="{width}"/>' for width in widths)
    xml.append('</w:tblGrid>')
    for index, row in enumerate([headers] + rows):
        xml.append('<w:tr><w:trPr><w:cantSplit/>' + ('<w:tblHeader/>' if index == 0 else '') + '</w:trPr>')
        for width, text in zip(widths, row):
            cell = f'<w:tcPr><w:tcW w:w="{width}" w:type="dxa"/>'
            if index == 0:
                cell += '<w:shd w:fill="163A5F"/>'
            elif index % 2:
                cell += '<w:shd w:fill="F1F5F9"/>'
            cell += '</w:tcPr>'
            rprops = '<w:rPr><w:b/><w:color w:val="FFFFFF"/></w:rPr>' if index == 0 else ''
            xml.append(f'<w:tc>{cell}<w:p><w:pPr><w:pStyle w:val="TableText"/></w:pPr>'
                       f'<w:r>{rprops}<w:t>{escape(str(text))}</w:t></w:r></w:p></w:tc>')
        xml.append('</w:tr>')
    xml.append('</w:tbl>')
    parts.append(''.join(xml))
    p()

p("ETHIOPIA JOB MATCHING", "Subtitle")
p("Three Approaches to Candidate Shortlisting", "Title")
p("LLM • BM25 • TF-IDF", "Subtitle")
p("Prepared 16 October 2026 | Explanation of the current project implementation", "Small")
title("1. Purpose and shared workflow")
p("The tool compares three ways of matching CVs to a job description (JD). Each method scores the same candidate pool, ranks candidates within that vacancy, and returns its own top-five shortlist. The methods remain separate so their results can be evaluated fairly.")
formula("JD + candidate CVs → score each CV → rank candidates → select five per method")
p("The default candidate pool follows the vacancy associations in the source manifest. An optional setting assesses every prepared CV against each selected JD. All methods use the same source text version, with method-specific processing recorded.")
table(["Method", "What it measures", "Score meaning"], [
    ["TF-IDF", "Similarity between weighted word vectors", "Cosine similarity, normally 0–1 for these nonnegative vectors"],
    ["BM25", "Keyword relevance with frequency saturation and CV-length adjustment", "Nonnegative relevance score; not restricted to 0–1"],
    ["LLM", "CV evidence supporting the JD requirement rubric", "Weighted supported-evidence coverage, 0–100"],
], [1600, 4200, 4400])
sub("What a shortlist does—and does not—mean")
p("Top-five membership means that a candidate ranked highly under that method. It does not establish eligibility, predict job performance, or give a probability of hiring. The tool keeps evidence and uncertainty visible for recruiter review.")
p("Candidates are ordered by descending score. Exact ties are broken by candidate ID, and ties at the fifth position are flagged. Unreadable documents go to review; if fewer than five candidates can be assessed, the output records a shortfall.")
sub("Current experiment")
p("The completed experiment covered 14 available JDs and 699 assessable synthetic CVs. Each method returned five candidates per JD: 42 shortlists and 210 shortlist entries overall. The LLM run used unconfirmed draft rubrics and is explicitly experimental. Independent recruiter judgments have not yet been supplied, so no method has been established as the most accurate.")
page()

title("2. TF-IDF: weighted word similarity")
p("TF-IDF stands for Term Frequency–Inverse Document Frequency. It gives greater importance to words that occur in a CV but are uncommon across the candidate pool.")
sub("Step 1 — Count terms")
p("Term frequency (TF) is the raw number of times a word appears in a CV. The current implementation lowercases text and uses individual word tokens of at least two word characters. It does not remove stop words or perform synonym expansion.")
sub("Step 2 — Calculate rarity weights")
formula("IDF(t) = ln[(1 + N) / (1 + DF(t))] + 1")
p("N is the number of CVs in the pool. DF(t) is the number of CVs containing term t at least once. The +1 terms smooth the calculation. A word occurring in fewer CVs receives a higher IDF.")
sub("Step 3 — Build vectors and compare")
formula("TF-IDF(t, CV) = TF(t, CV) × IDF(t)")
p("The vectorizer learns its vocabulary and IDF values from the CV pool, then transforms the JD using those same values. It applies L2 normalization and computes cosine similarity between the JD vector and each CV vector.")
formula("Cosine similarity = (JD · CV) / (||JD|| × ||CV||)")
sub("Worked example")
p("Suppose the JD is “Python forecasting” and the pool contains the three CV texts below. Python appears in two of the three CVs, giving IDF ≈ 1.288. Forecasting appears in one, giving IDF ≈ 1.693.")
table(["Candidate", "Simplified CV text", "Similarity"], [
    ["A", "Python forecasting", "1.000"],
    ["B", "Python", "0.605"],
    ["C", "Accounting", "0.000"],
], [1800, 6200, 2200])
p("Candidate A matches both weighted terms; B matches only Python; C shares neither term. A score of 0.605 is text similarity, not evidence that 60.5% of the job requirements are met.")
sub("Strengths and limitations")
p("TF-IDF is inexpensive, repeatable, and a useful baseline. However, the current word-based implementation can miss equivalent wording and cannot verify qualifications, distinguish positive from negated claims reliably, or calculate relevant years of experience. A JD with no vocabulary overlap produces an uninformative zero vector and is flagged.")
p("Implementation: 07-job-matching/tfidf/score.py", "Small")
page()

title("3. BM25: keyword relevance with diminishing returns")
p("BM25 is a document-ranking method. It adds a contribution for each matching JD term, combining term rarity, frequency within the CV, and an adjustment for CV length.")
sub("Step 1 — Weight rare terms")
formula("IDF(t) = ln[1 + (N − DF(t) + 0.5) / (DF(t) + 0.5)]")
p("N is the number of CVs; DF(t) is the number containing term t. This implementation uses a nonnegative IDF formulation, so rare matching words contribute more than common ones.")
sub("Step 2 — Calculate each matching term’s contribution")
formula("Contribution(t) = IDF(t) × TF(t) × (k1 + 1)")
formula("                         / [TF(t) + k1 × (1 − b + b × L / avgL)]")
p("TF(t) is the term count in the CV, L is its token count, and avgL is the average token count across CVs. The total BM25 score is the sum of contributions for unique JD terms.")
p("The current settings are k1 = 1.5 and b = 0.75. k1 controls how quickly the benefit from repeating a term levels off. b controls the strength of length adjustment: 0 means no adjustment; 1 applies the full relative-length adjustment.")
sub("Worked example")
p("Using the same JD, “Python forecasting,” and the same three CVs, the average CV length is 1.33 tokens. Applying the project’s BM25 formula gives:")
table(["Candidate", "Simplified CV text", "BM25 score"], [
    ["A", "Python forecasting", "1.184"],
    ["B", "Python", "0.530"],
    ["C", "Accounting", "0.000"],
], [1800, 6200, 2200])
p("A ranks first because it matches both words, including the rarer forecasting term. Repeating a term can raise a score, but the increase diminishes; ten mentions do not earn ten times the contribution of one mention.")
sub("Why it may outperform TF-IDF")
p("Frequency saturation can reduce the advantage from keyword repetition. Explicit CV-length adjustment provides another way to balance short and long documents. These properties often make BM25 a strong retrieval baseline, but they do not guarantee better candidate selection.")
p("Both current lexical methods still depend on matching words. BM25 does not independently interpret qualifications or verify experience. Its scores depend on the JD and candidate pool and should not be compared directly across methods or unrelated vacancies.")
p("Implementation: 07-job-matching/bm25/score.py", "Small")
page()

title("4. LLM: requirement-by-requirement evidence assessment")
p("A large language model (LLM) can interpret wording and context. In this tool, OpenAI assesses each candidate independently against a fixed JD requirement rubric. Python—not the LLM—calculates the aggregate score.")
sub("Step 1 — Define the rubric")
p("Each requirement has an ID, text, weight, and applicability setting. Draft requirements are extracted from JD sections for review. Current drafts use equal weights. Reviewed rubrics are required by default; experimental mode permits drafts without changing their confirmation status.")
sub("Step 2 — Classify the CV evidence")
table(["Evidence state", "Meaning"], [
    ["Supported", "The CV contains evidence supporting the requirement."],
    ["Explicitly not met", "The CV contains evidence establishing that the requirement is not met."],
    ["Unknown", "Information is missing or unclear; absence is not established."],
    ["Not applicable", "The rubric marks this requirement as not applicable."],
], [2600, 7600])
p("Supported and explicitly-not-met assessments require a quoted passage and source location. The application verifies literal source text, can resolve a unique matching location while retaining the original citation, and requests corrections for invalid responses. Unresolved errors leave that JD/method incomplete.")
sub("Step 3 — Calculate supported-evidence coverage")
formula("Score = 100 × supported requirement weights / applicable requirement weights")
table(["Illustrative requirement", "Weight", "Evidence"], [
    ["Python experience", "3", "Supported"],
    ["Forecasting experience", "2", "Supported"],
    ["Relevant master’s degree", "2", "Unknown"],
    ["SQL experience", "1", "Supported"],
], [5700, 1000, 3500])
p("In this illustrative weighted rubric, supported weight is 3 + 2 + 1 = 6, and applicable weight is 8. The score is 75. Unknown requirements receive no supported-evidence points but remain explicitly identified as unknown. Not-applicable requirements are excluded from the denominator.")
sub("Strengths and limitations")
p("The LLM can recognize related phrases and produce requirement-level evidence. It can also misinterpret a passage, overlook information, or produce incorrect citations. Checking that a quote exists does not prove that it supports the requirement. Structured responses, validation, retries, caching, and versioned settings improve traceability but do not guarantee correctness or identical uncached outputs.")
p("Implementation: 07-job-matching/llm/score.py", "Small")
page()

title("5. Comparing the approaches fairly")
p("Use identical JDs, candidate pools, and source text versions. Keep method settings fixed for final evaluation. Recruiters should assess suitability against an agreed rubric without seeing algorithm identities, scores, or ranks.")
table(["Criterion", "TF-IDF", "BM25", "LLM"], [
    ["Main signal", "Weighted word-vector similarity", "Weighted keyword relevance", "Requirement-level evidence"],
    ["Related wording", "Limited without expansion", "Limited without expansion", "Can interpret related wording"],
    ["Repeated terms", "Raw counts before normalization", "Diminishing contribution", "Depends on evidence interpretation"],
    ["Length handling", "L2 vector normalization", "Explicit relative-length adjustment", "Input-size limit; no automatic chunking"],
    ["Explanation", "Shared weighted terms", "Matching term contributions", "Evidence states and source quotes"],
    ["Operational cost", "Local computation", "Local computation", "API usage, latency, and possible retries"],
], [1900, 2700, 2700, 2900])
sub("Evaluation measures")
p("Precision@5: suitable candidates in the five shortlist positions divided by five. It requires judgments for every returned candidate; unfilled positions contribute zero.")
p("Recall@5: suitable shortlisted candidates divided by all suitable candidates in the pool. It requires complete pool judgments in this implementation and is undefined if no suitable candidates exist.")
p("NDCG@5: whether higher-relevance candidates appear nearer the top, compared with the best possible ordering. The implementation uses gain 2^relevance − 1 and logarithmic rank discount. Complete pool judgments are required; zero ideal gain makes the metric unavailable.")
p("Also compare shortlist overlap, runtime, API usage, and stability. Agreement is not proof of correctness. Runtime from cached LLM responses is not a fair measure of cold-run API latency. Do not compare raw BM25, cosine-similarity, and LLM scores numerically.")
sub("Project conclusions and next step")
p("No winner can be declared from the current outputs alone. The LLM experiment used draft rubrics, and independent recruiter judgments are still needed. Review the rubrics, label candidates beyond the three shortlists so missed suitable candidates can be identified, and evaluate methods per JD and across comparable vacancies.")
p("All approaches need checks for unequal errors across appropriately collected audit groups. Neither removing direct identifiers nor choosing a particular algorithm establishes fairness.")
sub("Implementation references")
p("TF-IDF: 07-job-matching/tfidf/score.py | BM25: 07-job-matching/bm25/score.py | LLM: 07-job-matching/llm/score.py | Metrics: 07-job-matching/comparison/evaluate.py", "Small")
p("Prepared from the project’s source code and documented live experiment. Worked-example scores use the current lexical implementations. This document describes the implemented methods rather than independently establishing their effectiveness.", "Small")

styles = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="{W}">
<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="21"/><w:color w:val="253449"/></w:rPr></w:rPrDefault>
<w:pPrDefault><w:pPr><w:spacing w:after="100" w:line="260" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>
<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:before="80" w:after="180"/></w:pPr><w:rPr><w:b/><w:color w:val="163A5F"/><w:sz w:val="44"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Subtitle"><w:name w:val="Subtitle"/><w:basedOn w:val="Normal"/><w:rPr><w:color w:val="367D89"/><w:sz w:val="25"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:outlineLvl w:val="0"/><w:spacing w:before="140" w:after="140"/></w:pPr><w:rPr><w:b/><w:color w:val="163A5F"/><w:sz w:val="30"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:outlineLvl w:val="1"/><w:spacing w:before="100" w:after="70"/></w:pPr><w:rPr><w:b/><w:color w:val="367D89"/><w:sz w:val="23"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Formula"><w:name w:val="Formula"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:after="90"/><w:shd w:fill="F1F5F9"/><w:ind w:left="140"/></w:pPr><w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/><w:sz w:val="19"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Small"><w:name w:val="Small"/><w:basedOn w:val="Normal"/><w:rPr><w:sz w:val="18"/><w:color w:val="5E6E7D"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="TableText"><w:name w:val="Table Text"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="20" w:line="230" w:lineRule="auto"/></w:pPr><w:rPr><w:sz w:val="19"/></w:rPr></w:style>
</w:styles>'''
document = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{W}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><w:body>{''.join(parts)}
<w:sectPr><w:footerReference w:type="default" r:id="rId2"/><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="850" w:right="850" w:bottom="850" w:left="850" w:header="360" w:footer="360"/></w:sectPr></w:body></w:document>'''
footer = f'''<w:ftr xmlns:w="{W}"><w:p><w:pPr><w:jc w:val="right"/></w:pPr><w:r><w:rPr><w:sz w:val="16"/><w:color w:val="5E6E7D"/></w:rPr><w:t>Ethiopia Job Matching | </w:t></w:r><w:fldSimple w:instr="PAGE"/></w:p></w:ftr>'''
content_types = '''<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>
</Types>'''
rels = '''<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'''
doc_rels = '''<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/></Relationships>'''
payload = {"[Content_Types].xml":content_types,"_rels/.rels":rels,"word/document.xml":document,
           "word/styles.xml":styles,"word/footer1.xml":footer,"word/_rels/document.xml.rels":doc_rels}
OUT.parent.mkdir(parents=True, exist_ok=True)
with ZipFile(OUT, "w", ZIP_DEFLATED) as archive:
    for name, xml in payload.items():
        ET.fromstring(xml)
        archive.writestr(name,xml.encode("utf-8"))
with ZipFile(OUT) as archive:
    assert archive.testzip() is None
    doc = ET.fromstring(archive.read("word/document.xml"))
    assert len(doc.findall(".//{"+W+"}tbl")) == 6
    assert len(doc.findall(".//{"+W+"}br")) == 4
print(str(OUT.resolve()))
print("Verified OOXML package, six tables, and five explicitly separated sections.")

