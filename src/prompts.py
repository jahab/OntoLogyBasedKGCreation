KG_EXTRACTION_PROMPT = """
You are an expert in legal knowledge graphs and ontology-based information extraction.

I will provide you:
1. A list of predefined ontology-based entity types and relationship types with descriptions
2. A legal text excerpts from which I want to extract structured graph data
3. A metadata of this case in json which includes fields like case_id, case_name and court_name.
4. A json which will depict what all entities have been already extracted which you can use as relevant information to do further extractions

 


Your job is to:
- Identify relevant entities (nodes) and relationships from the legal text **only using the ontology I provide**
- Use the relationship directions and entity types exactly as defined in the ontology
- Ensure that each extracted triple (node1)-[relationship]->(node2) follows the allowed schema
- Assign the proper properties to the nodes extracted based on the property table
- Output the triples in JSON format

Maintain Entity Consistency: When extracting entities, it's vital to ensure  consistency. If an entity, such as "John Doe", is mentioned multiple times in the text but is referred to by different names or pronouns (e.g., "Joe", "he"), always use the most complete identifier for that entity. The knowledge graph should be coherent and easily  understandable, so maintaining consistency in entity references is crucial.


The case metadata is provided so that you ensure consistency in extraction of nodes.

### Metadata
{metadata}


### Relevant Information
Here is the already extrcated nodes and relationships from this graph.
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

| Node1          | Property               | DataType  | Comment                                                                                                                                                                 |
|----------------|------------------------|-----------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| CatchWord      | catchwordValue         | string    | Descriptive words or phrases used to categorise the subject matter of a case along with some keywords representing the issues in the case                               |
| Court          | courtName              | string    |                                                                                                                                                                         |
| CourtCase      | hasCaseID              | string    |                                                                                                                                                                         |
| CourtCase      | hasCaseName            | string    |                                                                                                                                                                         |
| Court_Official | COFirstName            | string    |                                                                                                                                                                         |
| Court_Official | COLastName             | string    |                                                                                                                                                                         |
| DateOfJudgment | dateOfJudgment         | dateTime  |                                                                                                                                                                         |
| DateOfJudgment | hasDate                | int       |                                                                                                                                                                         |
| DateOfJudgment | hasMonth               | string    |                                                                                                                                                                         |
| DateOfJudgment | hasYear                | int       |                                                                                                                                                                         |
| Evidence       | evidenceLocation       | string    |                                                                                                                                                                         |
| Investigator   | hasDesignation         | string    |                                                                                                                                                                         |
| Investigator   | hasPolicePersonnelName | string    |                                                                                                                                                                         |
| Location       | locationName           | string    |                                                                                                                                                                         |
| Party          | firstName              | string    |                                                                                                                                                                         |
| Party          | lastName               | string    |                                                                                                                                                                         |
| Witness        | wFirstName             | string    |                                                                                                                                                                         |
| Witness        | wLastName              | string    |                                                                                                                                                                         |
| Witness        | witnessStatement       | string    |                                                                                                                                                                         |                                                                                                                                                                       |
| WordAndPhrase  | wordPhraseValue        | string    | words or phrases exctracted from the case to make the search better for the cases or find relevent cases or judgment                                                    |


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
*“Hrushikesh Roy presided over madras high court and delivered the final decision of setencing the accused to a find of 50000 INR in case CR/1987/11 on date 23 May 2023”*

Return only valid JSON. Do not wrap your output in markdown or text formatting.
Output:
{{"Data":
[
  {{
    "node1_type": "CourtCase",
    "node1_value": "CR/1987/11",
    "node2_type": "Judge",
    "node2_value": "Hrushikesh Roy",
    "relationship": "hasJudge"
  }},
  {{
    "node1_type": "Judge",
    "node1_value": "Hrushikesh Roy",
    "node2_type": "Court_Official",
    "node2_value": {{
      "COFirstName": "Hrushikesh",
      "COLastName": "Roy"
    }},
    "relationship": "is_a"
  }},
  {{
    "node1_type": "Judge",
    "node1_value": "Hrushikesh Roy",
    "node2_type": "Court",
    "node2_value": "Madras High Court",
    "relationship": "worksIn"
  }},
  {{
    "node1_type": "CourtCase",
    "node1_value": "CR/1987/11",
    "node2_type": "CourtDecision",
    "node2_value": "setencing the accused to a find of 50000 INR",
    "relationship": "hasFinalDecision"
  }},
  {{
    "node1_type": "CourtCase",
    "node1_value": "CR/1987/11",
    "node2_type": "DateOfJudgment",
    "node2_value": {{
      "dateOfJudgment": "2023-05-23",
      "hasDate": 23,
      "hasMonth": "May",
      "hasYear": 2023
    }},
    "relationship": "hasDateOfJudgment"
  }},
  {{
    "node1_type": "Madras High Court",
    "node1_value": "Madras High Court",
    "node2_type": "High_Court",
    "node2_value": "High_Court",
    "relationship": "is_a"
  }}
  ]
}}

"""


PROP_EXTRACTION_PROMPT = """

I am supplying you 2 nodes and their values with relationship. Additionally, I am also providing you the schema
and properties of the nodes. Your job is to fill the appropriate property based on the values you see. 
Do not add any extra node or properties from your end.

node1_type: {node1_type}
node1_value:  {node1_value}
relationship: {relationship}
node2_type: {node2_type}
node2_value:  {node2_value}

## Output Format 
{format_instructions}

return a well formatted json dict. Do not wrap your output in markdown or text formatting.
{{
"node1_type": {node1_type}
"node1_property" : {node1_property} # you are required to fill this up
"relationship": {relationship}
"node2_type": {node2_type}
"node2_property" : {node2_property} # you are required to fill this up
}}
"""

METADATA_EXTRACTION_PROMPT = """
Extract the following information from the provided text and return it as a JSON object:

- **case_id**: The case number.
- **court_name**: The name of the court.
- **case_name**: The names of the parties involved in the case.

## Output Format 
{format_instructions}
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