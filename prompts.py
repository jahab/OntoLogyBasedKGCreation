KG_EXTRACTION_PROMPT = """
You are an expert in legal knowledge graphs and ontology-based information extraction.

I will provide you:
1. A list of predefined ontology-based entity types and relationship types with descriptions
2. A few legal text excerpts from which I want to extract structured graph data

Your job is to:
- Identify relevant entities (nodes) and relationships from the legal text **only using the ontology I provide**
- Use the relationship directions and entity types exactly as defined in the ontology
- Ensure that each extracted triple (node1)-[relationship]->(node2) follows the allowed schema
- Assign the proper proties to the nodes extracted based on the property table
- Output the triples in JSON format


### Ontology:
Each row in the following table represents either a valid `is_a` hierarchy or a domain-range relationship.

| Node1              | Relationship | Node2  | Comment                                                |
|---------------------|--------------|--------|--------------------------------------------------------|
| Appellant           | is_a         | Party  | party who makes an appeal                              |
| District_Court      | is_a         | Courts_for_Civil | a term in judicial system in India in which a case is heard and judged by at least 2 judges |
| Review_Jurisdiction | is_a         | Jurisdiction | jurisdiction type is a review jurisdiction             |
| Order               | is_a         | CourtDecision | order given by the court                               |
| Place               | is_a         | Location | location name or place name                            |
| Criminal            | is_a         | CaseDomain | case is a criminal case                                |
| Individual          | is_a         | Party_Type | participants of the case are the individual persons    |
| Defendant           | is_a         | Party  | a person sued in the court of law                      |
| Judgement           | is_a         | CourtDecision | Judgement given by the judge                           |
| Appellant_Jurisdiction | is_a         | Jurisdiction | jurisdiction type is a appellant jurisdiction          |
| Judicial_Magistrate_Court(Second_Class) | is_a         | Courts_for_Criminal | lowest court after Judicial Magistrate Court (First Class) at distrcit level for criminal cases |
| Special_Bench | is_a         | Bench  | means the Bench constituted by or under the orders of the Chief Justice to hear a case or particular class of cases |
| IndianCourts | is_a         | Court  |                                                        |
| Solicitor  | is_a         | Court_Official | represents solicitor, learned counsel or laywer of the case |
| Metropolitan_Magistrate_Courts | is_a         | Courts_for_Criminal | lowest court after Chief Metropolitan Court at metropolitan level for criminal cases |
| Chief_Meterpolitan_Court | is_a         | Courts_for_Criminal | lower court at metropolitan level after Sessions Court for criminal cases |
| ObiterDictum | is_a         | Paragraph | additional obersvations, remarks, and opinions made by the judge that are not the part of the reason for the decision |
| Respondent | is_a         | Party  | party called upon to respond or answer a petition, a cliam or a appeal |
| Metropolitian_Courts | is_a         | IndianCourts | court for population more than 10 lakh city            |
| LearnedCounsel | is_a         | Court_Official | Learned counsel is a term of reference to the lawyers and advocates collectively in litigation |
| Fact       | is_a         | Paragraph | represents factual statements in the case law          |
| High_Court | is_a         | IndianCourts | court at the state level                               |
| Paragraph  | is_a         | Structure |                                                        |
| Tribunal   | is_a         | IndianCourts | represents the special courts for special issues or disputes |
| Sub_Court  | is_a         | Courts_for_Civil | second lower court in hierarchy at District level for civil cases |
| Courts_for_Civil | is_a         | CaseDomain | court for civil cases                                  |
| State      | is_a         | Location | represents state name/location                         |
| Division_Bench | is_a         | Bench  | a term in judicial system in India in which a case is heard and judged by at least 2 judges |
| Munsif_Court | is_a         | Courts_for_Civil | lowest court in heirarchy for civil ases at district level after Principal Junior Civil Court |
| Tribunal_Bench | is_a         | Bench  | Bench deals with tribunals cases                       |
| Concurrence | is_a         | Opinion | decisions result when a judge agrees with the ultimate conclusion made by the majority of the court but disagrees on how they reached that decision |
| Taluka     | is_a         | Location | represents taluka name/location                        |
| Majority   | is_a         | Opinion | Majority decisions are the ones where a majority of the judges agree |
| Plaintiff  | is_a         | Party  | party who brings the suit in the court of law          |
| Courts_of_Smaller_Causes | is_a         | Courts_for_Civil | lowest court after City Civil Courts at metropolitan level for civil cases |
| Organization | is_a         | Party_Type | organization(s) involved as the participant in the case |
| City_Civil_Courts | is_a         | Courts_for_Civil | lower court at metropolitan level after High Courts for civil cases |
| Argument   | is_a         | Paragraph | Argument made by any of the party                      |
| Issue      | is_a         | Paragraph | issues in the case arised by the party                 |
| Country    | is_a         | Location | A country                                              |
| Judicial_Magistrate_Court(First_Class) | is_a         | Courts_for_Criminal | second lower court at distrcit level after districit level Session Court for criminal cases |
| Person     | is_a         | Party_Type | A person                                               |
| District   | is_a         | Location | represents district name/location                      |
| Dissent    | is_a         | Opinion | judges who do not agree with the majority of the Court |
| Original_Jurisdiction | is_a         | Jurisdiction | jurisdiction type is a original jurisdiction           |
| Principal_Junior_Civil_Court | is_a         | Courts_for_Civil | third lower court in hierarchy at district level for civil cases |
| Decree     | is_a         | CourtDecision | formal order issued by the judges                      |
| RatioDecidendi | is_a         | Paragraph | the rationale for the decision                         |
| Civil      | is_a         | CaseDomain | case is a civil case                                   |
| Courts_for_Criminal | is_a         | CaseDomain | courts for crimnial cases                              |
| Session_Court | is_a         | Courts_for_Criminal | lower court at both distrcit and metropolitan level after High Courts specific for criminal cases |
| District_Court | is_a         | IndianCourts | a term in judicial system in India in which a case is heard and judged by at least 2 judges |
| Accussed   | is_a         | Party  | person against whom an allegation has been made that he has committed an offence, or who is charge with an offence |
| Opinion    | is_a         | Paragraph |                                                        |
| State      | is_a         | Party_Type | represents state name/location                         |
| Single_Judge | is_a         | Bench  | a case heard and judged by a single judge              |
| SupremeCourt | is_a         | IndianCourts | highest court in the judicial system                   |
| Advisory_Jurisdiction | is_a         | Jurisdiction | jurisdiction type is a advisory jurisdiction           |
| Writ_Jurisdiction | is_a         | Jurisdiction | jurisdiction type is a writ jurisdiction               |
| GovernmentOrganization | is_a         | Party_Type | party involved (either on both sides or any one) is the government in the case |
| Judge      | is_a         | Court_Official | A judge is a public official appointed to decide cases in a court of law. |
| Group      | is_a         | Party_Type | party of the case are the group of people on one side against another group of people or individual or state |
| Larger_Bench | is_a         | Bench  | a term in judicial system in India in which a case is heard and judged by three or five judges |
| Lawyer     | is_a         | Court_Official | Lawyer is a term of reference to the attroneys and advocates collectively in litigation |
| Petitioner | is_a         | Party  | one who makes the petition                             |
| Argument   | appellantArgument | Appellant | party who makes an appeal                              |
| Argument   | defendentArgument | Defendant | a person sued in the court of law                      |
| Argument   | petitionerArgument | Petitioner | one who makes the petition                             |
| Argument   | plaintiffArgument | Plaintiff | party who brings the suit in the court of law          |
| Argument   | respondentArgument | Respondent | party called upon to respond or answer a petition, a cliam or a appeal |
| Court      | hasCourtLoc  | Location | represents the location of the courts, etc and also used for evidence locations |
| Court      | hasDateOfJudgment | DateOfJudgment | signifies the final date on which the judgment is given by the court of law |
| Court      | hasJurisdiction | Jurisdiction | the extent to which a court of law can exercise its authority over any cases filed across a region |
| CourtCase  | cited        | CourtCase | represents the court judgment given by a court of law  |
| CourtCase  | hasAuthor    | Author | Author (Judge) who is responsible for a creation of case document |
| CourtCase  | hasBench     | Bench  | Defines the bench of the case.                         |
| CourtCase  | hasCourtOfficial | Court_Official | legal system related people involved in a case         |
| CourtCase  | hasEvidence  | Evidence | evidences presented in front of the court in the case  |
| CourtCase  | hasFact      | Fact   | represents factual statements in the case law          |
| CourtCase  | hasFinalDecision | CourtDecision | represents the decision made by the court of law in the one of the form of Decree, Judgment or Order. |
| CourtCase  | hasIssue     | Issue  | issues in the case arised by the party                 |
| CourtCase  | hasJudge     | Judge  | A judge is a public official appointed to decide cases in a court of law. |
| CourtCase  | hasObiterDictum | ObiterDictum | additional obersvations, remarks, and opinions made by the judge that are not the part of the reason for the decision |
| CourtCase  | hasParty     | Party  | party or people involved in the case                   |
| CourtCase  | hasPolicePersonnel | Investigator | A police officer is a warranted law employee of a police force |
| CourtCase  | hasProvision | Provision | clause or section number or article number applied/used in the case law |
| CourtCase  | hasRatioDecidendi | RatioDecidendi | the rationale for the decision                         |
| CourtCase  | hasRulingOf  | Court  | courts in the judicial system                          |
| CourtCase  | hasStatue    | Statute | includes the acts and norms of the law                 |
| CourtCase  | hasWitness   | Witness | witness involved/presented in the case                 |
| CourtCase  | hasWordPhrase | WordAndPhrase | words or phrases exctracted from the case to make the search better for the cases or find relevent cases or judgment |
| CourtCase  | hasWords     | CatchWord | Descriptive words or phrases used to categorise the subject matter of a case along with some keywords representing the issues in the case |
| Court_Official | worksIn      | Court  | courts in the judicial system                          |
| Evidence   | hasEvidenceLoc | Location | represents the location of the courts, etc and also used for evidence locations |
| Judge      | hasOpinion   | Opinion |                                                        |
| Judge      | withConcurrence | Concurrence | decisions result when a judge agrees with the ultimate conclusion made by the majority of the court but disagrees on how they reached that decision |
| Judge      | withDissent  | Dissent | judges who do not agree with the majority of the Court |
| Judge      | withMajority | Majority | Majority decisions are the ones where a majority of the judges agree |
| Party      | hasPartyType | Party_Type | represents the types of party involved in the case viz. individual, organization, govt. etc. |


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
  "<EntityType1>": "<EntityValue1>",
  "<EntityType2>": "<EntityValue2>",
  "relationship": "<OntologyRelationship>"
}}

### Example:
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


"""