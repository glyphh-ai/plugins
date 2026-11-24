# Documented indicators of fake / proxy applicants

## How the Resume Screener's fraud signals stand against this list

| Signal in the model | Documented here? |
|---|---|
| `location` (home against schools, jobs, phone) | Partly: foreign universities with a US address or history (1); phone or location differing between documents (11). An area code or time zone not fitting the stated home is **not** in any source opened (section 4): it is our own signal. |
| `name`, `shared` (same email or phone under other names) | Yes: reused phone numbers and email addresses (12), same contact information across applicants (2). The email address's own name not matching the applicant is **not** in a source opened. |
| `address` (mail drop, not fitting the home) | Only at hiring: a freight-forwarding or changed shipping address (27). In a resume it is our own signal. |
| `pattern` (same body, history or phrasing under other names) | Yes (2, 3). |
| `timestamps` | Only as login hours not matching the claimed location (29) and IP not matching the address (14): class b and c. |
| `aligned` (dates and facts that do not line up) | Only in general: "career inconsistencies" (8). Impossible or overlapping dates are **not** named by any source opened. |
| `built` (mirrors the posting, generic, wide skills, uncheckable) | Partly: mirrors the posting (5), over-polished generic text (6), a very broad skills list (9). Vague employers are **not** a named red flag in any source opened. |

Two things the sources say that bound what reading a resume can do: the schemes often use a **real person's stolen
or rented identity and a real work history** (section 2), which a resume read alone cannot tell from the real
person; and most documented indicators are class b or c (the channel, lookups, the interview), not the document.

Researched 2026-11-24. Class **a** = resume/cover letter alone; **b** = needs email, metadata or channel; **c** = needs lookups or live interaction. Quotes from [5][6] were read directly from PDF text; the rest were extracted by the fetch tool's reader model, so re-check wording.

## 1. Indicators

| # | Indicator | Class | Src | Quote |
|---|---|---|---|---|
| 1 | Degrees from Asian / non-North-American universities with a US address or US-only work history | a | [2][8] | "Education on resume is listed as universities in China, Japan, Singapore, Malaysia, or other Asian countries" |
| 2 | Same resume content under other applicants' names | a (across applicants) | [4][8] | "Cross-check HR systems for other applicants with the same resume content and/or contact information." |
| 3 | Waves of near-identical resumes for unrelated roles | a (across applicants) | [16] | "waves of nearly identical resumes for unrelated positions" |
| 4 | Typos and odd terminology | a | [4] | "Check applicant resumes for typos and unusual nomenclature." |
| 5 | Resume mirrors the job posting | a | [14] | "It reads like a near word-for-word match to the job description." |
| 6 | Over-polished, generic, buzzword text; big numbers without context | a | [14][15] | "There are big numbers but no context to back them up." |
| 7 | Keyword stuffing or hidden white text | a | [14] | "Hidden white text designed to manipulate ATS systems" |
| 8 | Career history that does not line up | a | [7] | "Better resume scanning for career inconsistencies." |
| 9 | Very broad skills list (described, not flagged) | a | [5] | "use of a wide variety of common languages, frameworks, tools, and cloud resources" |
| 10 | Small or mid-sized Western firms listed as employers (described, not flagged) | a | [5] | "names of small or mid-sized Western companies" |
| 11 | Phone or location differs between resume, cover letter and application form | a/b | [14] | "locations listed in their cover letter that don't align with what they've entered in your system" |
| 12 | Phone numbers and emails reused across applicants | b | [4][10] | "reused phone numbers (particularly voice-over-IP numbers) and email addresses" |
| 13 | Contact details wrong or changing | b | [5] | "Incorrect or changing contact information, specifically phone numbers and emails" |
| 14 | Application IP from anonymiser or not matching stated address | b | [14][9] | "IP address doesn't match listed address" |
| 15 | Same document templates across accounts | b | [5][6] | "the same templates being used across different developer accounts" |
| 16 | VoIP number, no footprint for contact details | c | [7][8][9] | "Use of VOIP numbers and lack of digital footprint for provided contact information" |
| 17 | Name, nationality, location, education, work history inconsistent across profiles | c | [5][6] | "Inconsistencies in name spelling, nationality, claimed work location, contact information, educational history, work history" |
| 18 | Online profiles do not match resume; several profiles with different photos, or none | c | [2][6] | "Social media and other online profiles that do not match the hired individual's provided resume" |
| 19 | Newly created or thin profiles | c | [10][14] | "New public profiles on LinkedIn, Twitter, GitHub, or freelancer platforms" |
| 20 | Will not appear on camera | c | [2][6] | "Unwillingness or inability to appear on camera" |
| 21 | Deepfake signs: lips and audio out of sync; artefacts when hand passes face | c | [1][9] | "passing a hand over a face, which disrupts facial landmark tracking" |
| 22 | Cannot answer questions about own location or education | c | [3][4] | "applicants being unable to field questions about where they are located" |
| 23 | Cheating on coding tests; long pauses, coached answers | c | [2][16] | "Indications of cheating on coding tests or when answering employment questionnaires" |
| 24 | Background check shows the PII belongs to someone else; E-Verify errors | c | [1][3] | "PII given by some of the applicants belonged to another individual" |
| 25 | Address and date of birth differ across sources; names inconsistent | c | [7][12] | "Discrepancies in address and date of birth across different sources" |
| 26 | References are email-only or other fake personas | c | [7][10] | "Use of other FAMOUS CHOLLIMA personas as job references" |
| 27 | Laptop shipping address differs from stated home, is a freight forwarder, or changes after hire | c | [2][3][5][7][8] | "Home address for provision of laptops or other company materials is a freight forwarding address" |
| 28 | Payment account changes, prepayment demands, crypto, account in another name | c | [2][5][6] | "Repeated requests for prepayment; anger or aggression when the request is denied." |
| 29 | Korean language settings; logins at hours not matching claimed location | c | [2][10] | "Language preferences are in Korean but the individual claims to be from a non-Korean speaking country" |

## 2. How the schemes build the fake applicant

- **Identity:** stolen or rented from real people; DOJ counted "more than 80 U.S. persons" compromised [11]; others sell or rent theirs [5][6][12].
- **Documents:** forged licences, social security cards and passports "combining the IT worker's own or a provided photo with the identifying information of a real person" [5]; AI face-swaps onto stolen documents and AI-enhanced headshots [7][8][12].
- **Work history:** profiles are filled "with the real affiliations and work experience of the proxy" [5]; resumes "exhibit significant overlap with publicly available resumes or are heavily reused" [8].
- **Employers:** small or mid-sized Western company names, real employees' names and look-alike email domains [5]; shell companies "with corresponding websites and financial accounts" [11].
- **Resume text:** GenAI used to "Generate and critique CVs and cover letters", test them against ATS software and auto-fill applications [13]; results are "more polished and lacking grammatical errors" [12].
- **Location:** VPN/VPS and third-country IPs [5]; US "laptop farms" where a facilitator hosts company laptops for remote access [8][11]; facilitators create job-site accounts and sit interviews [3].
- **Contact details:** new email and social accounts [12]; VoIP numbers [8]; many personas run from one console [13].
- **Online presence:** simple portfolio sites whose "contact information and location, as well as work history and education, is likely to be false" [5]; GitHub portfolios, fake LinkedIn, fake testimonials [8][12].
- **Interviews:** native English speakers hired to take calls [6]; real-time deepfakes let one operator "interview for the same position multiple times using different synthetic personas" [9].

## 3. Sources (all opened)

1. Deepfakes and Stolen PII Utilized to Apply for Remote Work Positions, FBI IC3, 2022-06-28, https://www.ic3.gov/PSA/2022/PSA220628
2. Additional Guidance on the DPRK Information Technology Workers, FBI IC3, 2023-10-18, https://www.ic3.gov/PSA/2023/PSA231018
3. DPRK Leverages U.S.-Based Individuals to Defraud U.S. Businesses and Generate Revenue, FBI IC3, 2024-05-16, https://www.ic3.gov/PSA/2024/PSA240516
4. North Korean IT Workers Conducting Data Extortion, FBI IC3, 2025-01-23, https://www.ic3.gov/PSA/2025/PSA250123
5. Guidance on the DPRK Information Technology Workers, US State/Treasury/FBI, 2022-05-16, https://ofac.treasury.gov/media/923126/download?inline
6. OFSI Advisory on North Korean IT Workers, UK HM Treasury OFSI, 2024-09-12, https://assets.publishing.service.gov.uk/media/68388290c99c4f37ab4e86b1/OFSI_Advisory_on_North_Korean_IT_Workers.pdf
7. How a North Korean Fake IT Worker Tried to Infiltrate Us, KnowBe4, 2024-07-23, https://blog.knowbe4.com/how-a-north-korean-fake-it-worker-tried-to-infiltrate-us
8. Staying a Step Ahead: Mitigating the DPRK IT Worker Threat, Google Cloud / Mandiant, 2024-09-23, https://cloud.google.com/blog/topics/threat-intelligence/mitigating-dprk-it-worker-threat
9. False Face: Unit 42 Demonstrates the Alarming Ease of Synthetic Identity Creation, Palo Alto Networks Unit 42, 2025-04-21, https://unit42.paloaltonetworks.com/north-korean-synthetic-identity-creation/
10. U.S. Government Disrupts FAMOUS CHOLLIMA Operation with CrowdStrike Assistance, CrowdStrike, date read as 2026-10-13 (unconfirmed), https://www.crowdstrike.com/en-us/blog/fbi-disrupts-famous-chollima-operation-with-crowdstrike-assistance/
11. Justice Department Announces Coordinated, Nationwide Actions to Combat North Korean Remote IT Workers' Schemes, US DOJ, 2025-06-30, https://www.justice.gov/opa/pr/justice-department-announces-coordinated-nationwide-actions-combat-north-korean-remote
12. Jasper Sleet: North Korean remote IT workers' evolving tactics to infiltrate organizations, Microsoft Threat Intelligence, 2025-06-30, https://www.microsoft.com/en-us/security/blog/2025/06/30/jasper-sleet-north-korean-remote-it-workers-evolving-tactics-to-infiltrate-organizations/
13. How AI services power the DPRK's IT contracting scams, Okta Threat Intelligence, 2025-04-24, https://sec.okta.com/articles/2025/04/GenAIDPRK/
14. Filtering Out the Fraud: How to Recognize Fake Candidates During the Hiring Process, Lever, 2026-04-17, https://www.lever.co/blog/filtering-out-the-fraud-how-to-recognize-fake-candidates-during-the-hiring-process/
15. Fake Resumes, Real Risks: How Tech Employers Can Prevent Fraud, Indeed, 2025-10-28, https://www.indeed.com/lead/fake-resumes-real-risks-how-tech-employers-can-prevent-fraud
16. Deepfakes, AI resumes, and the growing threat of fake applicants, Malwarebytes, 2025-12-09, https://www.malwarebytes.com/blog/inside-malwarebytes/2025/12/deepfakes-ai-resumes-and-the-growing-threat-of-fake-applicants

Could not open (not cited): DOJ May 2024 Chapman release, state.gov copy of [5], HireRight 2025 Benchmark release, Henle et al. 2019 resume-fraud paper. No Checkr, Sterling, South Korea or Japan list was opened.

## 4. Not found

No opened source states these:

- Impossible or overlapping dates (only "career inconsistencies" [7]).
- Area code or time zone not matching stated location.
- Identical formatting across applicants (only identical content [4][16], platform templates [5]).
- Email address patterns as an indicator.
- Vague or uncheckable employers as a named red flag.
- Unaccredited schools or diploma mills.
- Any measured accuracy or false-positive rate for a resume-only indicator.
