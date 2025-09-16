KG_EXTRACTION_PROMPT = """
You are an expert in building legal knowledge graphs and ontology-based information extraction.

I will provide you:
1. A list of predefined ontology-based entity types and relationship types with descriptions
2. A legal text excerpt from which you should extract structured graph data.
3. A metadata of this case in json which includes fields like case_id, case_name, court_name, parties involved etc.
4. A json which will depict what all entities have been already extracted which you can use as relevant information to do further extractions

Your job is to:
- Identify relevant entities (nodes) and relationships from the legal text **only using the ontology I provide**
- Use the relationship directions and entity types exactly as defined in the ontology
- Ensure that each extracted triple (node1)-[relationship]->(node2) follows the allowed schema
- Assign the proper properties to the nodes extracted based on the property table
- When multiple cases are mentioned using "WITH" or "AND," the first case mentioned should be considered the primary case, and all subsequent cases should be considered "cited" by the primary case. Each case mentioned in these clauses should be extracted as a CourtCase entity with its own hasCaseID.
- If you are unsure of any entity ot its properties then do not extract it. It is important that you do not hallucinate and do not give false or unverifiable information.
- When extracting individual names, case names, courtnames use only proper nouns. Do not use pronouns or common nouns
- Output the triples in JSON format

Use this thoughts while traversing the text
Thought: Think about how the extracted terms can have one on one relation with other terms based metadata and refrences provided. Do not deveiate from the ontology and DO NOT MAKE UP INFORMATION.


Maintain Entity Consistency: When extracting entities, it's vital to ensure consistency. If an entity, such as "John Doe", is mentioned multiple times in the text but is referred to by different names or pronouns (e.g., "Joe", "he"), always use the most complete identifier for that entity. The knowledge graph should be coherent and easily  understandable, so maintaining consistency in entity references is crucial.

The metadata is provided so that you ensure consistency in extraction of nodes.
### Metadata
{metadata}

### Relevant Information : This is the already extrcated nodes and relationships from the graph.
{relevant_info_graph}

### Ontology:
Each row in the following table represents either a valid `is_a` hierarchy or a domain-range relationship.

| Node1                                   | Relationship        | Node2                 | Comment                                                                                                             |
|-----------------------------------------|---------------------|-----------------------|---------------------------------------------------------------------------------------------------------------------|
| Appellant                               | is_a                | Party                 | party who makes an appeal                                                                                           |
| Defendant                               | is_a                | Party                 | a person sued in the court of law                                                                                   |
| Respondent                              | is_a                | Party                 | party called upon to respond or answer a petition, a cliam or a appeal                                              |
| Plaintiff                               | is_a                | Party                 | party who brings the suit in the court of law                                                                       |
| Accussed                                | is_a                | Party                 | person against whom an allegation has been made that he has committed an offence, or who is charge with an offence  |
| Petitioner                              | is_a                | Party                 | one who makes the petition                                                                                          |
| District_Court                          | is_a                | Courts_for_Civil      | a term in judicial system in India in which a case is heard and judged by at least 2 judges                         |
| Sub_Court                               | is_a                | Courts_for_Civil      | second lower court in hierarchy at District level for civil cases                                                   |
| Munsif_Court                            | is_a                | Courts_for_Civil      | lowest court in heirarchy for civil ases at district level after Principal Junior Civil Court                       |
| Courts_of_Smaller_Causes                | is_a                | Courts_for_Civil      | lowest court after City Civil Courts at metropolitan level for civil cases                                          |
| City_Civil_Courts                       | is_a                | Courts_for_Civil      | lower court at metropolitan level after High Courts for civil cases                                                 |
| Principal_Junior_Civil_Court            | is_a                | Courts_for_Civil      | third lower court in hierarchy at district level for civil cases                                                    |
| Review_Jurisdiction                     | is_a                | Jurisdiction          | jurisdiction type is a review jurisdiction                                                                          |
| Appellant_Jurisdiction                  | is_a                | Jurisdiction          | jurisdiction type is a appellant jurisdiction                                                                       |
| Writ_Jurisdiction                       | is_a                | Jurisdiction          | jurisdiction type is a writ jurisdiction               |
| Original_Jurisdiction                   | is_a                | Jurisdiction          | jurisdiction type is a original jurisdiction           |
| Advisory_Jurisdiction                   | is_a                | Jurisdiction          | jurisdiction type is a advisory jurisdiction           |
| Criminal                                | is_a                | CaseDomain            | case is a criminal case                                                                                             |
| Individual                              | is_a                | Party_Type            | participants of the case are the individual persons                                                                 |
| Organization                            | is_a                | Party_Type            | organization(s) involved as the participant in the case                                                             |
| Person                                  | is_a                | Party_Type            | A person                                                                                                            |
| State                                   | is_a                | Party_Type            | represents state name/location                                                                                      |
| GovernmentOrganization                  | is_a                | Party_Type            | party involved (either on both sides or any one) is the government in the case                                      |
| Group                                   | is_a                | Party_Type            | party of the case are the group of people on one side against another group of people or individual or state        |
| IndianCourts                            | is_a                | Court                 |                                                                                                                     |
| Solicitor                               | is_a                | Court_Official        | represents solicitor, learned counsel or laywer of the case                                                         |
| LearnedCounsel                          | is_a                | Court_Official        | Learned counsel is a term of reference to the lawyers and advocates collectively in litigation                      |
| Judge                                   | is_a                | Court_Official        | A judge is a public official appointed to decide cases in a court of law.                                           |
| Lawyer                                  | is_a                | Court_Official        | Lawyer is a term of reference to the attroneys and advocates collectively in litigation                             |
| Metropolitan_Magistrate_Courts          | is_a                | Courts_for_Criminal   | lowest court after Chief Metropolitan Court at metropolitan level for criminal cases                                |
| Chief_Meterpolitan_Court                | is_a                | Courts_for_Criminal   | lower court at metropolitan level after Sessions Court for criminal cases                                           |
| Judicial_Magistrate_Court(Second_Class) | is_a                | Courts_for_Criminal   | lowest court after Judicial Magistrate Court (First Class) at distrcit level for criminal cases                     |
| Judicial_Magistrate_Court(First_Class)  | is_a                | Courts_for_Criminal   | second lower court at distrcit level after districit level Session Court for criminal cases                         |
| Session_Court                           | is_a                | Courts_for_Criminal   | lower court at both distrcit and metropolitan level after High Courts specific for criminal cases                   |
| Metropolitian_Courts                    | is_a                | IndianCourts          | court for population more than 10 lakh city                                                                         |
| High_Court                              | is_a                | IndianCourts          | court at the state level                                                                                            |
| Tribunal                                | is_a                | IndianCourts          | represents the special courts for special issues or disputes                                                        |
| SupremeCourt                            | is_a                | IndianCourts          | highest court in the judicial system                   |
| District_Court                          | is_a                | IndianCourts          | a term in judicial system in India in which a case is heard and judged by at least 2 judges |
| ObiterDictum                            | is_a                | Paragraph             | additional obersvations, remarks, and opinions made by the judge that are not the part of the reason for the decision |
| Fact                                    | is_a                | Paragraph             | represents factual statements in the case law                                                                       |
| Opinion                                 | is_a                | Paragraph             |                                                        |
| RatioDecidendi                          | is_a                | Paragraph             | the rationale for the decision                         |
| Issue                                   | is_a                | Paragraph             | issues in the case arised by the party                 |
| Argument                                | is_a                | Paragraph             | Argument made by any of the party                      |
| Paragraph                               | is_a                | Structure             |                                                                                                                     |
| Courts_for_Civil                        | is_a                | CaseDomain            | court for civil cases                                                                                               |
| Civil                                   | is_a                | CaseDomain            | case is a civil case                                   |
| Courts_for_Criminal                     | is_a                | CaseDomain            | courts for crimnial cases                              |
| Division_Bench                          | is_a                | Bench                 | a term in judicial system in India in which a case is heard and judged by at least 2 judges                         |
| Tribunal_Bench                          | is_a                | Bench                 | Bench deals with tribunals cases                                                                                    |
| Larger_Bench                            | is_a                | Bench                 | a term in judicial system in India in which a case is heard and judged by three or five judges                      |
| Special_Bench                           | is_a                | Bench                 | means the Bench constituted by or under the orders of the Chief Justice to hear a case or particular class of cases |
| Single_Judge                            | is_a                | Bench                 | a case heard and judged by a single judge                                                                           |
| Majority                                | is_a                | Opinion               | Majority decisions are the ones where a majority of the judges agree                                                |
| Dissent                                 | is_a                | Opinion               | judges who do not agree with the majority of the Court                                                              |
| Concurrence                             | is_a                | Opinion               | decisions result when a judge agrees with the ultimate conclusion made by the majority of the court but disagrees on how they reached that decision |
| Taluka                                  | is_a                | Location              | represents taluka name/location                        |
| Country                                 | is_a                | Location              | A country                                              |
| District                                | is_a                | Location              | represents district name/location                      |
| State                                   | is_a                | Location              |           represents state name/location                         |
| Place                                   | is_a                | Location              | location name or place name                                                                                         |
| Order                                   | is_a                | CourtDecision         | order given by the court                                                                                            |
| Judgement                               | is_a                | CourtDecision         | Judgement given by the judge                                                                                        |
| Decree                                  | is_a                | CourtDecision         | formal order issued by the judges                      |
| Argument                                | appellantArgument   | Appellant             | party who makes an appeal                              |
| Argument                                | defendentArgument   | Defendant             | a person sued in the court of law                      |
| Argument                                | petitionerArgument  | Petitioner            | one who makes the petition                             |
| Argument                                | plaintiffArgument   | Plaintiff             | party who brings the suit in the court of law          |
| Argument                                | respondentArgument  | Respondent            | party called upon to respond or answer a petition, a cliam or a appeal |
| Court                                   | hasCourtLoc         | Location              | represents the location of the courts, etc and also used for evidence locations |
| Court                                   | hasDateOfJudgment   | DateOfJudgment        | signifies the final date on which the judgment is given by the court of law |
| Court                                   | hasJurisdiction     | Jurisdiction          | the extent to which a court of law can exercise its authority over any cases filed across a region |
| CourtCase                               | cited               | CourtCase             | represents the court judgment given by a court of law  |
| CourtCase                               | hasAuthor           | Author                | Author (Judge) who is responsible for a creation of case document |
| CourtCase                               | hasBench            | Bench                 | Defines the bench of the case.                         |
| CourtCase                               | hasCourtOfficial    | Court_Official        | legal system related people involved in a case         |
| CourtCase                               | hasEvidence         | Evidence              | evidences presented in front of the court in the case  |
| CourtCase                               | hasFact             | Fact                  | represents factual statements in the case law          |
| CourtCase                               | hasFinalDecision    | CourtDecision         | represents the decision made by the court of law in the one of the form of Decree, Judgment or Order. |
| CourtCase                               | hasIssue            | Issue                 | issues in the case arised by the party                 |
| CourtCase                               | hasJudge            | Judge                 | A judge is a public official appointed to decide cases in a court of law. |
| CourtCase                               | hasObiterDictum     | ObiterDictum          | additional obersvations, remarks, and opinions made by the judge that are not the part of the reason for the decision |
| CourtCase                               | hasParty            | Party                 | party or people involved in the case                   |
| CourtCase                               | hasPolicePersonnel  | Investigator          | A police officer is a warranted law employee of a police force |
| CourtCase                               | hasProvision        | Provision             | clause or section number or article number applied/used in the case law |
| CourtCase                               | hasRatioDecidendi   | RatioDecidendi        | the rationale for the decision                         |
| CourtCase                               | hasRulingOf         | Court                 | courts in the judicial system                          |
| CourtCase                               | hasStatue           | Statute               | includes the acts and norms of the law                 |
| CourtCase                               | hasWitness          | Witness               | witness involved/presented in the case                 |
| CourtCase                               | hasWordPhrase       | WordAndPhrase         | words or phrases exctracted from the case to make the search better for the cases or find relevent cases or judgment |
| CourtCase                               | hasWords            | CatchWord             | Descriptive words or phrases used to categorise the subject matter of a case along with some keywords representing the issues in the case |
| Court_Official                          | worksIn             | Court                 | courts in the judicial system                          |
| Evidence                                | hasEvidenceLoc      | Location              | represents the location of the courts, etc and also used for evidence locations |
| Judge                                   | hasOpinion          | Opinion               |                                                        |
| Judge                                   | withConcurrence     | Concurrence           | decisions result when a judge agrees with the ultimate conclusion made by the majority of the court but disagrees on how they reached that decision |
| Judge                                   | withDissent         | Dissent               | judges who do not agree with the majority of the Court |
| Judge                                   | withMajority        | Majority              | Majority decisions are the ones where a majority of the judges agree |
| Party                                   | hasPartyType        | Party_Type            | represents the types of party involved in the case viz. individual, organization, govt. etc. |


## Properties of Nodes:

| Node1          | Property               | DataType  | Comment                                                                                                                                   |
|----------------|------------------------|-----------|-------------------------------------------------------------------------------------------------------------------------------------------|
| CatchWord      | catchwordValue         | string    | Descriptive words or phrases used to categorise the subject matter of a case along with some keywords representing the issues in the case |
| Court          | courtName              | string    |                                                                                                                                           |
| CourtCase      | hasCaseID              | string    |                                                                                                                                           |
| CourtCase      | hasCaseName            | string    |                                                                                                                                           |
| Court_Official | COFirstName            | string    |                                                                                                                                           |
| Court_Official | COLastName             | string    |                                                                                                                                           |
| DateOfJudgment | dateOfJudgment         | dateTime  |                                                                                                                                           |
| DateOfJudgment | hasDate                | int       |                                                                                                                                           |
| DateOfJudgment | hasMonth               | string    |                                                                                                                                           |
| DateOfJudgment | hasYear                | int       |                                                                                                                                           |
| Evidence       | evidenceLocation       | string    |                                                                                                                                           |
| Investigator   | hasDesignation         | string    |                                                                                                                                           |
| Investigator   | hasPolicePersonnelName | string    |                                                                                                                                           |
| Location       | locationName           | string    |                                                                                                                                           |
| Party          | firstName              | string    |                                                                                                                                           |
| Party          | lastName               | string    |                                                                                                                                           |
| Witness        | wFirstName             | string    |                                                                                                                                           |
| Witness        | wLastName              | string    |                                                                                                                                           |
| Witness        | witnessStatement       | string    |                                                                                                                                           |
| WordAndPhrase  | wordPhraseValue        | string    | words or phrases exctracted from the case to make the search better for the cases or find relevent cases or judgment                      |
| CourtDecision  | text                   | string    |                                                                                                                                           |
| Argument       | text                   | string    |                                                                                                                                           |
| Opinion        | text                   | string    |                                                                                                                                           |
| Paragraph      | text                   | string    |                                                                                                                                           |
| Fact           | text                   | string    |                                                                                                                                           |
| Structure      | text                   | string    |                                                                                                                                           |

Please ensure your extraction **strictly uses** only these node types and relationships.

### Output format (for each extracted relation):
Each extracted triple should look like this:
{{
  "<EntityType1>": "<OntologyEntityName>",
  "<Entityvalue1>": "<ExtractedfromText>",
  "<EntityType2>": "<OntologyEntityName>",
  "<Entityvalue2>": "<ExtractedfromText>",
  "relationship": "<OntologyRelationship>"
}}

An Entity Value cannot be an Entitytype. If you find that any EntityType cannot have a value leave that value blank.
Example of a wrong relationship:

{{"node1_type": "Appellant",
   "node1_value": "Chunthuram",
   "node2_type": "Party_Type",
   "node2_value": "Individual",
   "relationship": "hasPartyType"}}
node2_value is assigned as an entity and it is incorrect
Correct json would be 
{{"node1_type": "Appellant",
   "node1_value": "Chunthuram",
   "node2_type": "Individual",
   "node2_value": "",
   "relationship": "hasPartyType"}}

Individual is an EntityType and not EntityValue.

### Example on how to extract entities:
For the sentence:  
*“Hrushikesh Roy presided over madras high court and delivered the Judgement of setencing person A to a fine of 50000 INR in case CR/1987/11 under section 41 of CrPC on date 23 May 2023 citing Civil Rule No.8574 (w) of 1983 as precedent.”*

Return only valid JSON. Do not wrap your output in markdown or text formatting.
Output:
{{
  "Data": [
    {{
      "node1_type": "CourtCase",
      "node1_value": {{
        "hasCaseID": "CR/1987/11"
      }},
      "node2_type": "Court",
      "node2_value": {{
        "courtName": "madras high court"
      }},
      "relationship": "hasRulingOf"
    }}, 
    {{
      "node1_type": "CourtCase",
      "node1_value": {{
        "hasCaseID": "CR/1987/11"
      }},
      "node2_type": "Judge",
      "node2_value": {{
        "COFirstName": "Hrushikesh",
        "COLastName": "Roy"
      }},
      "relationship": "hasJudge"
    }},
    {{
      "node1_type":"CourtCase",
      "node1_value": {{
        "hasCaseID": "CR/1987/11"
      }},
      "node2_type":"CourtCase",
      "node2_value": {{
        "hasCaseID": "Civil Rule No.8574 (w) of 1983"
      }},
      "relationship": "cited"
    }},
    {{
      "node1_type": "Judge",
      "node1_value": {{
        "COFirstName": "Hrushikesh",
        "COLastName": "Roy"
      }},
      "node2_type": "Court",
      "node2_value": {{
        "courtName": "madras high court"
      }},
      "relationship": "worksIn"
    }},
    {{
      "node1_type": "CourtCase",
      "node1_value": {{
        "hasCaseID": "CR/1987/11"
      }},
      "node2_type": "Accussed",
      "node2_value": "person A",
      "relationship": "hasParty"
    }},
    {{
      "node1_type": "Accussed",
      "node1_value": "person A",
      "node2_type": "Individual",
      "node2_value": "",
      "relationship": "hasPartyType"
    }},
    {{
      "node1_type": "CourtCase",
      "node1_value": {{
        "hasCaseID": "CR/1987/11"
      }},
      "node2_type": "Judgement",
      "node2_value": "sentencing person A to a fine of 50000 INR",
      "relationship": "hasFinalDecision"
    }},
    {{
      "node1_type": "CourtCase",
      "node1_value": {{
        "hasCaseID": "CR/1987/11"
      }},
      "node2_type": "Provision",
      "node2_value": "Section 41 of CrPC",
      "relationship": "hasProvision"
    }},
  ]
}}
"""


# PROP_EXTRACTION_PROMPT = """
# I am supplying you 2 nodes and their values with relationship. Additionally, I am also providing you the schema
# and properties of the nodes. Your job is to fill the appropriate property based on the values you see. 
# If and only if the node_property is empty or {{}} or  "" then use "text" as key and nothing else.
# Do not add any extra node or properties from your end.

# node1_type: {node1_type}
# node1_value:  {node1_value}
# relationship: {relationship}
# node2_type: {node2_type}
# node2_value:  {node2_value}

# ## Output Format 
# {format_instructions}

# return a well formatted json dict. Do not wrap your output in markdown or text formatting.
# {{
# "node1_type": {node1_type}
# "node1_property" : {node1_property} # you are required to fill this up
# "relationship": {relationship}
# "node2_type": {node2_type}
# "node2_property" : {node2_property} # you are required to fill this up
# }}
# """





PROP_EXTRACTION_PROMPT = """
You are given two nodes and their values with a relationship. Your job is to fill the provided node_property objects only using the given node_value(s). Follow these rules exactly.
Rules  
1. DO NOT add or remove node types, properties, or nodes. Use only the keys already present in node1_property and node2_property. Never introduce new property names.
2. When to use "text":
  - Use "text" if and only if the provided nodeX_property is empty — that means either {{}} (an empty dict) or "" (an empty string). In that case, set nodeX_property to {{"text": nodeX_value}} and nothing else.
3. When property keys exist (even if they are empty strings)
  - Always use the provided keys. Do not replace them with "text".
  - If nodeX_value is a dictionary/object and contains keys matching any property keys, copy those values into the corresponding property keys.
  - If nodeX_value is a plain string and the property keys exist then assign the values based on best logic.
  - If no best logic can be found then stuff everything in first key. For example. node1_value: "state of Haryana" then correct assignment will be  {{"firstName":"State of Haryana", "lastName":""}} and incorrect assignment will be {{"firstName":"State", "lastName":"of Haryana"}}. So dont act dumb. 
5. Return a well formatted json dict. Do not wrap your output in markdown or text formatting.

Input  
node1_type: {node1_type}
node1_value: {node1_value} # This is given to you
node1_property : {node1_property} # you are required to fill this up based on node1_value
relationship: {relationship}
node2_type: {node2_type}
node2_value: {node2_value} # This is given to you
node2_property : {node2_property} # you are required to fill this up based on node2_value

## Output Format 
{format_instructions}

## Example 1
  - ###Input
  node1_type: CourtCase
  node1_value: {{'hasCaseID': 'Sessions Case No.149/2001'}}
  node1_property: {{'neutralCitations': '', 'hasCaseID': '', 'equivalentCitation': '', 'hasCaseName': ''}}
  relationship: hasParty
  node2_type: Accussed
  node2_value: Jagan Ram
  node2_property: {{'firstName': '', 'lastName': ''}}

  - ###Output
  {{
    "node1_type": "CourtCase",
    "node1_property": {{
      "neutralCitations": "",
      "hasCaseID": "Sessions Case No.149/2001",
      "equivalentCitation": "",
      "hasCaseName": ""
    }},
    "relationship": "hasParty",
    "node2_type": "Accussed",
    "node2_property": {{
      "firstName": "Jagan",
      "lastName": "Ram"
    }}
  }}
## Example 2
  - ###Input
  node1_type: CourtCase
  node1_value: {{'hasCaseID': 'Sessions Case No.149/2001'}}
  node1_property: {{'neutralCitations': '', 'hasCaseID': '', 'equivalentCitation': '', 'hasCaseName': ''}}
  relationship: hasFact
  node2_type: Fact
  node2_value: "person retruning from the market"
  node2_property: {{}}

  - ###Output
  {{
    "node1_type": "CourtCase",
    "node1_property": {{
      "neutralCitations": "",
      "hasCaseID": "Sessions Case No.149/2001",
      "equivalentCitation": "",
      "hasCaseName": ""
    }},
    "relationship": "hasFact",
    "node2_type": "Fact",
    "node2_property": {{
      "text": "person retruning from the market"
    }}
  }}

## Example 3
  - ###Input
  node1_type: CourtCase
  node1_value: {{'hasCaseID': 'Sessions Case No.149/2001'}}
  node1_property: {{'neutralCitations': '', 'hasCaseID': '', 'equivalentCitation': '', 'hasCaseName': ''}}
  relationship: hasOpinion
  node2_type: Opinion
  node2_value: {{"text": "need to do reassessment of the forensics. Bail denied to the party."}}
  node2_property: {{}}

  - ###Output
  {{
    "node1_type": "CourtCase",
    "node1_property": {{
      "neutralCitations": "",
      "hasCaseID": "Sessions Case No.149/2001",
      "equivalentCitation": "",
      "hasCaseName": ""
    }},
    "relationship": "hasOpinion",
    "node2_type": "Opinion",
    "node2_property": {{"text": "need to do reassessment of the forensics. Bail denied to the party."}}
  }}

## Example 4
  - ###Input
  node1_type: CourtCase
  node1_value: {{'hasCaseID': 'Sessions Case No.149/2001'}}
  node1_property: {{'neutralCitations': '', 'hasCaseID': '', 'equivalentCitation': '', 'hasCaseName': ''}}
  relationship: hasEvidence
  node2_type: Evidence
  node2_value: {{"evidence_location": "Sector 33 Markeytard", "evidence_type":"fingerprints"}}
  node2_property: {{}}

  - ###Output
  {{
    "node1_type": "CourtCase",
    "node1_property": {{
      "neutralCitations": "",
      "hasCaseID": "Sessions Case No.149/2001",
      "equivalentCitation": "",
      "hasCaseName": ""
    }},
    "relationship": "hasEvidence",
    "node2_type": "Evidence",
    "node2_property": {{"text": "Sector 33 Markeytard fingerprints"}}
  }}
"""



METADATA_REFINE_PROMPT = """
You are required to extract the follwoing from the given text. If some of fields are not present do not output them. Do not add any extra information other than these fields.
Return output as string.
Extract:
-court_name: The name of the court.
-court_type: District_Court/SupremeCourt/Tribunal/High_Court/Metropolitian_Courts/Session_Court
-case_name: The names of the parties involved in the case.
-case_id: The case number.
-Judge: Name of the Judge
-Lawyer: Name of the Lawyer
-Counsel: Name of the Councel
-Solicitor: Name of the Solicitor
-court_decision: Order/Judgement/Decree
-Appellant: Name of Appellant
-Defendant: Name of Defendant
-Respondent: Name of Respondent
-Plaintiff: Name of Plaintiff
-Accused: Name of Plaintiff 
-Petitioner: Name of Petitioner
-DateOfJudgement: Date 
-citations: citation to a Case/ Act/ Law/ Article
"""


METADATA_EXTRACTION_PROMPT = """
You are an expert in building legal knowledge graphs and ontology-based information extraction.

I will provide you:
1. A list of predefined ontology-based entity types and relationship types with descriptions
2. A legal text excerpt from which you should extract structured graph data.

Your job is to:
- Identify relevant entities (nodes) and relationships from the legal text **only using the ontology I provide**
- Use the relationship directions and entity types exactly as defined in the ontology
- Ensure that each extracted triple (node1)-[relationship]->(node2) follows the allowed schema
- Assign the proper properties to the nodes extracted based on the property table
- When multiple cases are mentioned using "WITH" or "AND," the first case mentioned should be considered the primary case, and all subsequent cases should be considered "cited" by the primary case. Each case mentioned in these clauses should be extracted as a CourtCase entity with its own hasCaseID.
- If you are unsure of any entity ot its properties then do not extract it. It is important that you do not hallucinate and do not give false or unverifiable information.
- Output the triples in JSON format
- Do not add any new information on your own.

### Schema

| Node1                                   | Relationship | Node2               | Comment                                                                                                             |
|-----------------------------------------|--------------|---------------------|---------------------------------------------------------------------------------------------------------------------|
| Appellant                               | is_a         | Party               | party who makes an appeal                                                                                           |
| Defendant                               | is_a         | Party               | a person sued in the court of law                                                                                   |
| Respondent                              | is_a         | Party               | party called upon to respond or answer a petition, a cliam or a appeal                                              |
| Plaintiff                               | is_a         | Party               | party who brings the suit in the court of law                                                                       |
| Accussed                                | is_a         | Party               | person against whom an allegation has been made that he has committed an offence, or who is charge with an offence  |
| Petitioner                              | is_a         | Party               | one who makes the petition                                                                                          |
| District_Court                          | is_a         | Courts_for_Civil    | a term in judicial system in India in which a case is heard and judged by at least 2 judges                         |
| Sub_Court                               | is_a         | Courts_for_Civil    | second lower court in hierarchy at District level for civil cases                                                   |
| Munsif_Court                            | is_a         | Courts_for_Civil    | lowest court in heirarchy for civil ases at district level after Principal Junior Civil Court                       |
| Courts_of_Smaller_Causes                | is_a         | Courts_for_Civil    | lowest court after City Civil Courts at metropolitan level for civil cases                                          |
| City_Civil_Courts                       | is_a         | Courts_for_Civil    | lower court at metropolitan level after High Courts for civil cases                                                 |
| Principal_Junior_Civil_Court            | is_a         | Courts_for_Civil    | third lower court in hierarchy at district level for civil cases                                                    |
| Review_Jurisdiction                     | is_a         | Jurisdiction        | jurisdiction type is a review jurisdiction                                                                          |
| Appellant_Jurisdiction                  | is_a         | Jurisdiction        | jurisdiction type is a appellant jurisdiction                                                                       |
| Writ_Jurisdiction                       | is_a         | Jurisdiction        | jurisdiction type is a writ jurisdiction                                                                            |
| Original_Jurisdiction                   | is_a         | Jurisdiction        | jurisdiction type is a original jurisdiction                                                                        |
| Advisory_Jurisdiction                   | is_a         | Jurisdiction        | jurisdiction type is a advisory jurisdiction                                                                        |
| Individual                              | is_a         | Party_Type          | participants of the case are the individual persons                                                                 |
| Organization                            | is_a         | Party_Type          | organization(s) involved as the participant in the case                                                             |
| Person                                  | is_a         | Party_Type          | A person                                                                                                            |
| State                                   | is_a         | Party_Type          | represents state name/location                                                                                      |
| GovernmentOrganization                  | is_a         | Party_Type          | party involved (either on both sides or any one) is the government in the case                                      |
| Group                                   | is_a         | Party_Type          | party of the case are the group of people on one side against another group of people or individual or state        |
| IndianCourts                            | is_a         | Court               |                                                                                                                     |
| Solicitor                               | is_a         | Court_Official      | represents solicitor, learned counsel or laywer of the case                                                         |
| LearnedCounsel                          | is_a         | Court_Official      | Learned counsel is a term of reference to the lawyers and advocates collectively in litigation                      |
| Judge                                   | is_a         | Court_Official      | A judge is a public official appointed to decide cases in a court of law.                                           |
| Lawyer                                  | is_a         | Court_Official      | Lawyer is a term of reference to the attroneys and advocates collectively in litigation                             |
| Metropolitan_Magistrate_Courts          | is_a         | Courts_for_Criminal | lowest court after Chief Metropolitan Court at metropolitan level for criminal cases                                |
| Chief_Meterpolitan_Court                | is_a         | Courts_for_Criminal | lower court at metropolitan level after Sessions Court for criminal cases                                           |
| Judicial_Magistrate_Court(Second_Class) | is_a         | Courts_for_Criminal | lowest court after Judicial Magistrate Court (First Class) at distrcit level for criminal cases                     |
| Judicial_Magistrate_Court(First_Class)  | is_a         | Courts_for_Criminal | second lower court at distrcit level after districit level Session Court for criminal cases                         |
| Session_Court                           | is_a         | Courts_for_Criminal | lower court at both distrcit and metropolitan level after High Courts specific for criminal cases                   |
| Metropolitian_Courts                    | is_a         | IndianCourts        | court for population more than 10 lakh city                                                                         |
| High_Court                              | is_a         | IndianCourts        | court at the state level                                                                                            |
| Tribunal                                | is_a         | IndianCourts        | represents the special courts for special issues or disputes                                                        |
| SupremeCourt                            | is_a         | IndianCourts        | highest court in the judicial system                                                                                |
| District_Court                          | is_a         | IndianCourts        | a term in judicial system in India in which a case is heard and judged by at least 2 judges                         |
| Courts_for_Civil                        | is_a         | CaseDomain          | court for civil cases                                                                                               |
| Civil                                   | is_a         | CaseDomain          | case is a civil case                                                                                                |
| Courts_for_Criminal                     | is_a         | CaseDomain          | courts for crimnial cases                                                                                           |
| Criminal                                | is_a         | CaseDomain          | case is a criminal case                                                                                             |
| Division_Bench                          | is_a         | Bench               | a term in judicial system in India in which a case is heard and judged by at least 2 judges                         |
| Tribunal_Bench                          | is_a         | Bench               | Bench deals with tribunals cases                                                                                    |
| Larger_Bench                            | is_a         | Bench               | a term in judicial system in India in which a case is heard and judged by three or five judges                      |
| Special_Bench                           | is_a         | Bench               | means the Bench constituted by or under the orders of the Chief Justice to hear a case or particular class of cases |
| Single_Judge                            | is_a         | Bench               | a case heard and judged by a single judge                                                                           |
| Taluka                                  | is_a         | Location            | represents taluka name/location                                                                                     |
| Country                                 | is_a         | Location            | A country                                                                                                           |
| District                                | is_a         | Location            | represents district name/location                                                                                   |
| State                                   | is_a         | Location            | represents state name/location                                                                                      |
| Place                                   | is_a         | Location            | location name or place name                                                                                         |
| Order                                   | is_a         | CourtDecision       | order given by the court                                                                                            |
| Judgement                               | is_a         | CourtDecision       | Judgement given by the judge                                                                                        |
| Decree                                  | is_a         | CourtDecision       | formal order issued by the judges                                                                                   |
| CourtCase                               | hasJudge     | Judge               | A judge is a public official appointed to decide cases in a court of law.                                           |
| Court                                   | hasCourtLoc  | Location            | represents the location of the courts, etc and also used for evidence locations                                     |
| Court                                   | hasJurisdiction| Jurisdiction      | the extent to which a court of law can exercise its authority over any cases filed across a region                  |
| CourtCase                               | cited          | CourtCase         | represents the court judgment given by a court of law                                                               |
| CourtCase                               | hasAuthor      | Author            | Author (Judge) who is responsible for a creation of case document                                                   |
| CourtCase                               | hasParty       | Party             | party or people involved in the case                                                                                |
| CourtCase                               | hasRulingOf    | Court             | courts in the judicial system                                                                                       |
| Court_Official                          | worksIn        | Court             | courts in the judicial system                                                                                       |
| Party                                   | hasPartyType   | Party_Type        | represents the types of party involved in the case viz. individual, organization, govt. etc.                        |
| CourtCase                               | hasProvision   | Provision         | includes the acts and norms of the law                 |


## Properties of Nodes:

| Node1          | Property           | DataType |
|----------------|--------------------|----------|
| Court          | courtName          | string   |
| CourtCase      | hasCaseID          | string   |
| CourtCase      | hasCaseName        | string   |
| CourtCase      | equivalentCitation | string   |
| CourtCase      | neutralCitations   | string   |
| DateOfJudgment | dateOfJudgment     | dateTime |
| DateOfJudgment | hasDate            | int      |
| DateOfJudgment | hasMonth           | string   |
| DateOfJudgment | hasYear            | int      |
| Location       | locationName       | string   |


-court_name: The name of the court.
-court_type: District_Court/SupremeCourt/Tribunal/High_Court/Metropolitian_Courts/Session_Court
-case_name: The names of the parties involved in the case.
-case_id: The case number.
-Court Official: Judge/Lawyer/Counsel
-court_decision: Order/Judgement/Decree
-Appellant 
-Defendant
-Respondent
-Plaintiff
-Accused
-Petitioner
-DateOfJudgement
-citations: citation to a Case/ Act/ Law/ Article

## Output Format 
### Output format (for each extracted relation):
Each extracted triple should look like this:
{{
  "<EntityType1>": "<OntologyEntityName>",
  "<Entityvalue1>": "<ExtractedfromText>",
  "<EntityType2>": "<OntologyEntityName>",
  "<Entityvalue2>": "<ExtractedfromText>",
  "relationship": "<OntologyRelationship>"
}}


An Entity Value cannot be an Entitytype. If you find that any EntityType cannot have a value leave that value blank.
Example of a wrong relationship:

{{"node1_type": "Appellant",
   "node1_value": "Chunthuram",
   "node2_type": "Party_Type",
   "node2_value": "Individual",
   "relationship": "hasPartyType"}}
node2_value is assigned as an entity and it is incorrect
Correct json would be 
{{"node1_type": "Appellant",
   "node1_value": "Chunthuram",
   "node2_type": "Individual",
   "node2_value": "",
   "relationship": "hasPartyType"}}

### Example on how to extract entities:
TEXT:
"
IN THE SUPREME COURT OF INDIA
CRIMINAL APPELLATE JURISDICTION
CRIMINAL APPEAL NO.1115 OF 2010
BALVIR SINGH …Appellant
VERSUS
STATE OF MADHYA PRADESH …Respondent
WITH
CRIMINAL APPEAL NO.1116 OF 2010
BHAV SINGH …Appellant
VERSUS
STATE OF MADHYA PRADESH …Respondent
CRIMINAL APPEAL NO.1119 OF 2010
HARNAM SINGH …Appellant
VERSUS
STATE OF MADHYA PRADESH …Respondent
J U D G M E N T
R. BANUMATHI, J.
These appeals arise out of the judgment dated 26.08.2008 passed by the High Court of Judicature at Madhya Pradesh at Jabalpur in and by which the High Court affirmed
the conviction of the appellants (Accused No.1 to 4) under Sections 341, 302 and 302 read with 34 IPC and the sentence of imprisonment for life imposed upon each of the accused
"
Return only valid JSON. Do not wrap your output in markdown or text formatting.
Output:
{{"Data":
[
    {{
    "node1_type": "CourtCase",
    "node1_value": {{"hasCaseName": "Balvir Singh Versus State of Madhya Pradesh", "hasCaseID":"CRIMINAL APPEAL NO.1115 OF 2010"}},
    "node2_type": "Court",
    "node2_value": "Supreme Court of India",
    "relationship": "hasRulingOf"
  }},
  {{
    "node1_type": "Court",
    "node1_value": "Supreme Court of India",
    "node2_type": "Appellant_Jurisdiction",
    "node2_value": "",
    "relationship": "hasJurisdiction"
  }},
  
  {{
    "node1_type": "CourtCase",
    "node1_value": {{"hasCaseName": "Balvir Singh Versus State of Madhya Pradesh", "hasCaseID":"CRIMINAL APPEAL NO.1115 OF 2010"}},
    "node2_type": "Appellant",
    "node2_value": "BALVIR SINGH",
    "relationship": "hasParty"
  }},
  
  {{
    "node1_type": "Party",
    "node1_value": "BALVIR SINGH",
    "node2_type": "Individual",
    "node2_value": "",
    "relationship": "hasPartyType"
  }},
  
  {{
    "node1_type": "Party",
    "node1_value": "State of Madhya Pradesh",
    "node2_type": "State",
    "node2_value": "",
    "relationship": "hasPartyType"
  }},
  
  {{
    "node1_type": "CourtCase",
    "node1_value": {{"hasCaseName": "Balvir Singh Versus State of Madhya Pradesh", "hasCaseID":"CRIMINAL APPEAL NO.1115 OF 2010"}},
    "node2_type": "Respondent",
    "node2_value":  "State of Madhya Pradesh",
    "relationship": "hasParty"
  }},
  
  {{
    "node1_type": "CourtCase",
    "node1_value": {{"hasCaseName": "Balvir Singh Versus State of Madhya Pradesh", "hasCaseID":"CRIMINAL APPEAL NO.1115 OF 2010"}},
    "node2_type": "Judge",
    "node2_value": "R. Banumathi",
    "relationship": "hasJudge"
  }},
  {{
    "node1_type": "Judge",
    "node1_value": "R. Banumathi",
    "node2_type": "Court",
    "node2_value": "Supreme Court of India",
    "relationship": "worksIn"
  }},
  {{
    "node1_type": "CourtCase",
    "node1_value": {{"hasCaseName": "Balvir Singh Versus State of Madhya Pradesh", "hasCaseID":"CRIMINAL APPEAL NO.1115 OF 2010"}},
    "node2_type": "CourtCase",
    "node2_value":  {{"hasCaseName": "Bhav Singh Versus State of Madhya Pradesh", "hasCaseID":"CRIMINAL APPEAL NO.1116 OF 2010"}},
    "relationship": "cited"
  }},
    {{
    "node1_type": "CourtCase",
    "node1_value": {{"hasCaseName": "Balvir Singh Versus State of Madhya Pradesh", "hasCaseID":"CRIMINAL APPEAL NO.1115 OF 2010"}},
    "node2_type": "CourtCase",
    "node2_value":  {{"hasCaseName": "Harnam Singh Versus State of Madhya Pradesh", "hasCaseID":"CRIMINAL APPEAL NO.1119 OF 2010"}},
    "relationship": "cited"
  }},
  
  {{
    "node1_type": "CourtCase",
    "node1_value": {{"hasCaseName": "Balvir Singh Versus State of Madhya Pradesh", "hasCaseID":"CRIMINAL APPEAL NO.1115 OF 2010"}},
    "node2_type": "Court",
    "node2_value": "Supreme Court of India",
    "relationship": "hasRulingOf"
  }},
  {{
    "node1_type": "CourtCase",
    "node1_value": {{"hasCaseName": "Balvir Singh Versus State of Madhya Pradesh", "hasCaseID":"CRIMINAL APPEAL NO.1115 OF 2010"}},
    "node2_type": "Judgement",
    "node2_value": "",
    "relationship": "hasFinalDecision"
  }},
  {{
    "node1_type": "CourtCase",
    "node1_value": {{"hasCaseName": "Balvir Singh Versus State of Madhya Pradesh", "hasCaseID":"CRIMINAL APPEAL NO.1115 OF 2010"}},
    "node2_type": "Provision",
    "node2_value": "Section 341 of IPC",
    "relationship": "hasProvision"
  }},
  {{
    "node1_type": "CourtCase",
    "node1_value": {{"hasCaseName": "Balvir Singh Versus State of Madhya Pradesh", "hasCaseID":"CRIMINAL APPEAL NO.1115 OF 2010"}},
    "node2_type": "Provision",
    "node2_value": "Section 302 of IPC",
    "relationship": "hasProvision"
  }}
  ]
}}
"""




REFINE_NODES_PROMPT = """
You are given two nodes with their labels properties. Based on the nodes supplied your task is tell me if these two nodes can be merged or not.
Answer yes only and only if you are super super confident.
Answer in just `yes` or `no`. Do not add any extra/other information from your end otherwise my system will break.
Node 1:
{node1}

Node2:
{node2}

## Examples

"""
EXTRACT_COURTCASE_DETAILS_PROMPT = """
Extract the following information from the provided text and return it as a JSON object:

- **case_id**: The case number.
- **court_name**: The name of the court.
- **case_name**: The names of the parties involved in the case.

## EXAMPLE
{{"hasCaseName": "Balvir Singh Versus State of Madhya Pradesh", 
"hasCaseID":"Criminal Appeal No.1115 Of 2010"}}

## Output Format 
{format_instructions}
"""