from langchain_community.document_loaders import PyPDFLoader
from langchain.docstore.document import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

import pandas as pd
import os
from neo4j import GraphDatabase
import json
from vector_store import  *
from prompts import *
from output_parser import *
import bm25s

def get_node_labels(tx):
    result = tx.run("CALL db.labels()")
    return [record["label"] for record in result]

def get_relationship_types(tx):
    result = tx.run("CALL db.relationshipTypes()")
    return [record["relationshipType"] for record in result]


def get_property_keys(tx):
    result = tx.run("CALL db.propertyKeys()")
    return [record["propertyKey"] for record in result]

def get_label_connections(tx):
    query = """
    MATCH (a)-[r]->(b)
    RETURN DISTINCT labels(a)[0] AS from_label, type(r) AS rel_type, labels(b)[0] AS to_label
    """
    return list(tx.run(query))


def getAllRelationships(tx):
    query = """
    MATCH (child:Resource)-[:n4sch__SCO]->(parent:Resource)
    RETURN 
      child.`n4sch__name` AS from_node,
      "is_a" AS relation,
      parent.`n4sch__name` AS to_node,
      child.`n4sch__comment` as comment

    UNION
    
    // // Object property relationships
    MATCH (r:Resource:n4sch__Relationship)
    MATCH (r)-[:n4sch__DOMAIN]->(domain:Resource)
    MATCH (r)-[:n4sch__RANGE]->(range:Resource)
    RETURN 
      domain.`n4sch__name` AS from_node,
      r.`n4sch__name` AS relation,
      range.`n4sch__name` AS to_node,
      range.`n4sch__comment` as comment
    ORDER BY from_node, relation, to_node, comment
    """
    return list(tx.run(query))


def get_all_properties(tx):
    query = """
    MATCH (prop:Resource:n4sch__Property)
    MATCH (prop)<-[:n4sch__DOMAIN]->(prop_domain:Resource)
    MATCH (prop)<-[:n4sch__RANGE]->(prop_range:Resource)
    RETURN 
      prop_domain.`n4sch__name` AS from_node,
      prop.`n4sch__name` AS property,
      prop_range.`n4sch__name` AS datatype
    ORDER BY from_node, property, datatype
    """
    return list(tx.run(query))


def get_subclasses(tx):
    query = """
    MATCH (child:Resource)-[:n4sch__SCO]->(parent:Resource)
    RETURN 
        child.`n4sch__name` AS SubClass,
        parent.`n4sch__name` AS SuperClass
        ORDER BY SuperClass, SubClass
    
    """
    return list(tx.run(query))

def get_properties(tx):
    query = """
        MATCH (c:Resource)-[:n4sch__SPO]->(parent:Resource)
        RETURN c.n4sch__name, parent.n4sch__name
    """
    return pd.DataFrame(tx.run(query))



def find_subclass(tx, node):
    query = """
        OPTIONAL MATCH (subclass:n4sch__Class {n4sch__name: $node})-[:n4sch__SCO]->(superclass:n4sch__Class)
        WITH subclass, superclass
        WHERE superclass IS NOT NULL
        RETURN subclass.n4sch__name AS child, superclass.n4sch__name AS parent
        UNION
        // Fallback: Try to find subclasses of Party
        MATCH (superclass:n4sch__Class {n4sch__name: $node})<-[:n4sch__SCO]-(subclass:n4sch__Class)
        RETURN subclass.n4sch__name AS child, superclass.n4sch__name AS parent
    """
    return list(tx.run(query, node = node))


def find_property(tx,node):
    query = """
        MATCH (n {n4sch__name: $node})  // or MATCH (n:Judge) if Judge is a label
        MATCH path = (n)<-[:n4sch__DOMAIN]-(root:n4sch__Property)
        RETURN DISTINCT n.n4sch__name AS ancestorClass, root.n4sch__name AS property
    """
    return list(tx.run(query, node = node))

def get_ontology_in_graph(tx):
    #This link has same schema as the legalOntology.owl file
    query = """
        CALL n10s.graphconfig.init();
        CREATE CONSTRAINT n10s_unique_uri FOR (r:Resource) REQUIRE r.uri IS UNIQUE;
        CALL n10s.onto.import.fetch("https://pastebin.com/raw/jWHtDRy5","Turtle"); 
    """
    tx.run("CALL n10s.graphconfig.init();")
    tx.run("CREATE CONSTRAINT n10s_unique_uri FOR (r:Resource) REQUIRE r.uri IS UNIQUE;")
    tx.run("""
           CALL n10s.onto.import.fetch("https://pastebin.com/raw/jWHtDRy5","Turtle"); 
           """)




def load_ontology(driver):
    
    def is_graph_config_initialized(tx):
        result = tx.run("CALL n10s.graphconfig.show()")
        return result.single() is not None
    # 1. Create graph config (can be in one transaction)
    def init_graph_config(tx):
        tx.run("CALL n10s.graphconfig.init()")

    # 2. Create constraint (must be in its own transaction)
    def create_rdf_constraint(tx):
        tx.run("CREATE CONSTRAINT n10s_unique_uri IF NOT EXISTS FOR (r:Resource) REQUIRE r.uri IS UNIQUE")

    # 3. Load the ontology (data operation, must be in a separate transaction)
    def load_ontology_from_link(tx):
        tx.run("""
            CALL n10s.onto.import.fetch("https://pastebin.com/raw/jWHtDRy5", "Turtle")
        """)
    
    with driver.session() as session:
        if not session.execute_read(is_graph_config_initialized):
            session.execute_write(lambda tx: tx.run("CALL n10s.graphconfig.init()"))
    
    with driver.session() as session:
        session.execute_write(create_rdf_constraint)
    
    with driver.session() as session:
        session.execute_write(load_ontology_from_link)



def create_index(driver):
    def _create_index(tx):
        query = """
        CREATE TEXT INDEX  paragraph IF NOT EXISTS FOR (n:Paragraph) ON (n.text) 
        """
        tx.run(query)
        
    with driver.session() as session:
        res = session.execute_write(_create_index)

def create_constraint(driver):
    def _create_constraint(tx):
        query = """
        CREATE CONSTRAINT courtcase_unique
        FOR (n:CourtCase) REQUIRE (n.hasCaseID) IS UNIQUE
        """
        tx.run(query)
    
    def _check_contraint_exists(tx):
        query = """
        SHOW CONSTRAINTS YIELD name
        WHERE name = 'courtcase_unique'
        RETURN count(*) > 0 AS exists
        """
        return tx.run(query).single()["exists"]
    
    with driver.session() as session:
        res = session.execute_read(_check_contraint_exists)    
        if res:
            print(f"{res}  Constraint already exists..")
            return
        else:
            print("Creating Constraint on CourtCase with property hasCaseID..")
            res = session.execute_write(_create_constraint)  

def fetch_relationship_from_ontology(driver):
    allowed_relationships = []
    with driver.session() as session:
        edges = session.execute_read(getAllRelationships)
        for e in edges:
            allowed_relationships.append(tuple([e["from_node"], e["relation"], e["to_node"], e['comment']]))
    return allowed_relationships

def fetch_properties_from_ontology(driver)->list:
    allowed_properties = []
    with driver.session() as session:
        edges = session.execute_read(get_all_properties)
        for e in edges:
            allowed_properties.append(tuple([e["from_node"], e["property"], e["datatype"]]))
    return allowed_properties

def format_relationships_in_md(allowed_relationships:list)->list:
    rows = []
    for index, (n1, rel, n2, comment) in enumerate(allowed_relationships):
        if comment == None:
            comment = ""    
        rows.append(f"| {n1:<10} | {rel:<12} | {n2:<6} | {comment:<54} |")

    header =  "| Node1                            | Relationship                        | Node2                                 | Comment                                                                                                          |"
    divider = "|----------------------------------|-------------------------------------|---------------------------------------|------------------------------------------------------------------------------------------------------------------|"
    markdown_table = "\n".join([header, divider] + rows)
    print(markdown_table)

def format_properties_in_md(allowed_properties:list)->list:
    rows = []
    for index, (n1, rel, n2) in enumerate(allowed_properties):
        if comment == None:
            comment = ""    
        rows.append(f"| {n1:<10} | {rel:<12} | {n2:<6}    |")

    header =  "| Node1                    | Property                     | DataType                      |                                             |"
    divider = "|--------------------------|------------------------------|-------------------------------|---------------------------------------------|"
    markdown_table = "\n".join([header, divider] + rows)
    print(markdown_table)



def check_valid_relationship(tx, node1, relationship, node2):
    """
    Take a nodes and relationship as input and return if node and relationship exist or not
    If True tx.run will return three nodes
    If Flase tx.run will return empty list
    """
    query = """
        MATCH (n1:n4sch__Class {n4sch__name: $node1})
        MATCH (n2:n4sch__Class {n4sch__name: $node2})
        MATCH (r:n4sch__Relationship {n4sch__name: $relationship})
        MATCH (r)-[:n4sch__DOMAIN]->(n1)
        MATCH (r)-[:n4sch__RANGE]->(n2)
        RETURN n1, r, n2
    """
    return list(tx.run(query,node1 = node1,relationship=relationship, node2 = node2))


def refine_parent_child_relation(driver, node1_type, node2_type, node1_val, node2_val, relationship):
    """
    function to handle is_a (is subclassof relation ship)
    It was observed from LLM that some nodes with is_a relationsip were not getting correctly outputted.
    The functions aims to find the appropriate parent and child for a given node
    if the parent child relationship is incorrect then interchange them to correct order
    Returns: node and relationship in correct order 
    """
    # print("Relation Not Found.. Checking for subclasses")
    print(f"[refine_parent_child_relation]",node1_type, node2_type)
    invalid_node = True
    with driver.session() as session:
        subclasses_nodes = session.execute_read(find_subclass, node1_type) 
    # print(subclasses_nodes)
    for sc in subclasses_nodes:
        if (node1_type == sc['child'] and node2_type == sc['parent']):
            # print(sc['child'], sc['parent'])
            # print("=========relation_correct")
            invalid_node = False
            break
        elif(node1_type == sc['parent'] and node2_type == sc['child']):
            node1_type = sc['child']
            node2_type = sc['parent']
            temp = node1_val
            node1_val = node2_val
            node2_val = temp
            invalid_node = False
            break
        else:
            invalid_node = True
    return node1_type, node2_type, node1_val, node2_val, invalid_node


def get_constraints_for_label(tx, label):
    query = """
    SHOW CONSTRAINTS YIELD name, type, labelsOrTypes, properties
    WHERE $label IN labelsOrTypes
    RETURN properties
    """
    result = tx.run(query, label=label)
    return [r["properties"] for r in result]  # List of lists



def get_constraints_for_label(tx, label):
    query = """
    SHOW CONSTRAINTS YIELD name, type, labelsOrTypes, properties
    WHERE $label IN labelsOrTypes
    RETURN properties
    """
    result = tx.run(query, label=label)
    return [r["properties"] for r in result]  # List of lists

def get_nodes_by_label(tx, label):
    query = """
    MATCH (n:{}) RETURN n;
    """
    result = tx.run(query.format(label))
    return [r["n"] for r in result]  # List of lists


# FIXME: CRITICAL: BM25 retreiver does not work well with a small corpus.
#  If the len(node_corpus) = 1, 2, 3 BM25 will fail.
# Need a fall back mechanism on using local embeddings. Or find a way to merge the query --> Fixed but flaky

def merge_node(tx, labels, value):
    for key,val in value.items():
        if val is None:
            value[key] = ""
    # Handle single or multiple labels
    label_str = ":" + ":".join(labels) if isinstance(labels, list) else f":{labels}"
    label = labels[0] if isinstance(labels, list) else labels
    retriever = None
    # Step 1: Check for node key constraint
    constrained_keys_list = get_constraints_for_label(tx, label)
    print(f"=constrained_keys_list= {constrained_keys_list}")
    node_corpus = []
    if constrained_keys_list:
        d = get_nodes_by_label(tx, label)
        print(d)
        # collect all the information of the nodes in a string and 
        # append it to list to make a corpus for BM25 search
        for node in d:
            tmp_str = ""
            for key, val in node.items():
                if key in constrained_keys_list[0]:
                    tmp_str = tmp_str + f"{key}:{val}, "
            node_corpus.append(tmp_str) 
        # this contains the information of all nodes based on a given a label
        # ["CourtCase1 - properties", "CourtCase2 - properties" ..]
        print(f"node_corpus {node_corpus}")
        if node_corpus:
            retriever = bm25s.BM25(corpus=node_corpus)
            retriever.index(bm25s.tokenize(node_corpus))
        
        if retriever:
            query = ""
            for key,val in value.items():
                if val == None:
                    val = ""
                if key in constrained_keys_list[0]:
                    query = query+f"{key}:{val} "
            print(f"--query to BM 25: {query}")
            results, scores = retriever.retrieve(bm25s.tokenize(query), k=1)
            print(f"{results} {scores}")
            if scores[0][0]>1:
                index = node_corpus.index(results[0][0])        
                for key, val in d[index].items():
                    if val:
                        constrained_keys_list[0].append(key)
                        if value[key] == "": # update the value key if key is available in graph but not in model
                            value[key] = val
                        print(f"+++ {value[key]},  {key},  {val}")
                constrained_keys_list[0] = list(set(constrained_keys_list[0]))
  
                # nodes = [hascaseanme:"session case bhavanisingh vs state", hascaseid:"1234/554",
                #          hascaseanme:"chunturam vs state of chattisgarph", hascaseid:"513/2002",
                #          hascaseanme:"lalsingh vs bsingh", hascaseid:"sxdc/ppoi",
                #          ]

                # value = hascaseanme:"chunturam vs state of chattisgarph", hascaseid:"",
            else:
                for node in d:
                    print(f"----- {node}")
                    for cs_key in constrained_keys_list[0]:
                        if node.get(cs_key) != None:
                            if node[cs_key] == value[cs_key]:
                                print("comes here")
                                for key_v,val_v in value.items():
                                    if val_v=='':
                                        value[key_v] = node[key_v]
                        
                constrained_keys_list[0] = list(set(constrained_keys_list[0]))
            
    # constrained_keys_list = constrained_keys_list
    # Step 2: Choose a constraint if available
    constrained_keys = None
    for keys in constrained_keys_list:
        if all(k in value for k in keys):  # Only use if all keys are available in the data
            constrained_keys = keys
            break

    print(f"constrained_keys {constrained_keys}")
    if constrained_keys:
        # Use only constraint keys in MERGE
        merge_props = ", ".join(f"{k}: ${k}" for k in constrained_keys)
        query = f"MERGE (n{label_str} {{ {merge_props} }})"

        # Now SET all the other properties (excluding merge keys)
        
        set_props = [k for k in value if k not in constrained_keys]
        
        if set_props:
            set_clause = ", ".join(f"n.{k} = ${k}" for k in set_props)
            query += f"\nSET {set_clause}"

        print(f"[merge_node:] using constraint keys: {constrained_keys}")
        for key,val in value.items():
            if val is None:
                value[key] = ""
        tx.run(query, **value)

    else:
        # No constraints — fallback to using all props
        props = ", ".join(f"{k}: ${k}" for k in value)
        query = f"MERGE (n{label_str} {{ {props} }})"
        print("[merge_node] : no constraints, merging on all props")
        tx.run(query, **value)

def merge_relationship(tx, node1_type, node1_value, node2_type, node2_value, relationship):
    def format_labels(label):
        return ":" + ":".join(label) if isinstance(label, list) else f":{label}"

    print(f"{node1_type} {node1_value} {node2_type} {node2_value} {relationship}")
    node1_label_str = format_labels(node1_type)
    node2_label_str = format_labels(node2_type)
    print(f"{node1_label_str} { node2_label_str}")
    # Build node1 match
    # node1_params = {}
    # if isinstance(node1_value, dict):
    #     node1_match = " AND ".join(f"n1.{k} = ${k}1" for k in node1_value)
    #     for k, v in node1_value.items():
    #         node1_params[f"{k}1"] = v
    # else:
    #     key = f"{node1_type[-1].lower()}Name" if isinstance(node1_type, list) else f"{node1_type.lower()}Name"
    #     node1_match = f"n1.{key} = $node1_value"
    #     node1_params["node1_value"] = node1_value

    # # Build node2 match
    # node2_params = {}
    # if isinstance(node2_value, dict):
    #     node2_match = " AND ".join(f"n2.{k} = ${k}2" for k in node2_value)
    #     for k, v in node2_value.items():
    #         node2_params[f"{k}2"] = v
    # else:
    #     key = f"{node2_type[-1].lower()}Name" if isinstance(node2_type, list) else f"{node2_type.lower()}Name"
    #     node2_match = f"n2.{key} = $node2_value"
    #     node2_params["node2_value"] = node2_value

    # print("=========",node1_match, node2_match)
    # Combine WHERE clause safely
    # where_clauses = []
    # if node1_match:
    #     where_clauses.append(node1_match)
    # if node2_match:
    #     where_clauses.append(node2_match)

    # where_clause = " AND ".join(where_clauses)

    # WHERE {where_clause}
    props1 = ", ".join(f"{k}: $n1_{k}" for k in node1_value)
    props2 = ", ".join(f"{k}: $n2_{k}" for k in node2_value)
    
    # TODO: FIXME: This needs to change 
    # props1:{"chunk_id":"qaws"}
    # props2:{"chunk_id":"edrftg"}
    # params = {**node1_value, **node2_value} = {"chunk_id":"edrftg"} -->this is like merge my argument. and two arguments cannot be same 
    
    query = f"""
        MATCH (n1{node1_label_str} {{{props1}}}) 
        MATCH (n2{node2_label_str} {{{props2}}})
        MERGE (n1)-[r:{relationship}]->(n2)
    """
    params = {}
    for k, v in node1_value.items():
        if v is None:
            params[f"n1_{k}"] = ""
        else:
            params[f"n1_{k}"] = v
    for k, v in node2_value.items():
        if v is None:
            params[f"n2_{k}"] = ""
        else:
            params[f"n2_{k}"] = v
    # Merge all parameters
    # params = {**node1_value, **node2_value}

    # print("Query:\n", query)
    # print("Params:", params)
    print(f"[merge_relationship] query: {query} params : {params}")
    tx.run(query, **params)


# What I wnat to do: If I am at a node the find all its parents. and Find all its properties.
# To find all the parents first I need to know all the subclasses

# First Lets find all the parents-> 
def merged_node_with_label_and_prop(driver,node:str)->dict:
    node_labels = []
    node_properties = {}
    def _find_labels_and_properties(driver, node):
        with driver.session() as session:
            subclass_nodes = session.execute_read(find_subclass, node)
            props = session.execute_read(find_property, node)
            for prop in props:
                node_properties[prop["property"]] = ""
        for sc_node in subclass_nodes:
            if sc_node["parent"] == node:
                return
            node_labels.append(sc_node["parent"])
            _find_labels_and_properties(driver, sc_node["parent"])
    node_labels.append(node)
    _find_labels_and_properties(driver, node)
    node_dict = {"properties":node_properties, "labels": node_labels}
    return node_dict




def some_func_v2(driver, prop_ex_chain, node1_type, node1_value, relationship, node2_type,  node2_value):
    if relationship == "is_a":
        # Check if the extracted node is a valid subclass or not. If not then return with valid sublassing
        node1_type, node2_type, node1_value, node2_value,invalid_node = refine_parent_child_relation(driver, node1_type,node2_type,node1_value,node2_value,relationship)
        if invalid_node ==  True:
            print("Invalid Node relationship in subclass:", node1_type, relationship, node2_type)
            print("====================")
            return
        return
    node1_dict = merged_node_with_label_and_prop(driver, node1_type) # {'properties': {'COLastName': '', 'COFirstName': ''},'labels': ['Judge', 'Court_Official']}
    node2_dict = merged_node_with_label_and_prop(driver, node2_type)
    # check if a valid relationship exists in ontology for between these node types
    print(f"[some_func_v2]:\n node1_dict: {node1_dict} \n node2_dict: {node2_dict}")
    for label_1 in node1_dict['labels']:
        for label_2 in node2_dict['labels']:
            with driver.session() as session:
                edges = session.execute_read(check_valid_relationship, label_1, relationship, label_2) 
                for e in edges:
                    print(f"[TRIPLE in FUNC:] {node1_type},  {node1_dict["properties"]}, {e["r"]["n4sch__name"]}, {node2_type}, {node2_dict["properties"]}")
                    print(f"[TRIPLE TO EXTRACT:] {e["n1"]["n4sch__name"]}, {node1_dict["properties"]}, {node1_value}, {e["r"]["n4sch__name"]}, {e["n2"]["n4sch__name"]}, {node2_dict["properties"]}, {node2_value}")
                    dc = prop_ex_chain.invoke({"node1_type": node1_type, "node2_type": node2_type,
                                       "relationship":relationship, 
                                       "node1_value":node1_value, "node2_value":node2_value,
                                       "node1_property":json.dumps(node1_dict["properties"]), "node2_property":json.dumps(node2_dict["properties"]),
                                       })
                    print(f"[MODEL OUTPUT:] {dc}")
                    return {"node1_dict":node1_dict,"node2_dict":node2_dict, "model_output":dc}
                    

def get_nodes_and_rels(tx):
    query = """
    MATCH p = (n)-[r]->(s)
    WHERE NOT n:n4sch__Class AND NOT n:n4sch__Relationship AND NOT n:n4sch__Property AND NOT n:Resource AND NOT n:_GraphConfig AND NOT n:_NsPrefDef 
    AND NOT s:n4sch__Class AND NOT s:n4sch__Relationship AND NOT s:n4sch__Property AND NOT n:Resource AND NOT n:_GraphConfig AND NOT n:_NsPrefDef
    return n,r,s
    """
    return list(tx.run(query)) 


def get_graph(driver):
    def format_node(node):
        labels = list(node.labels)
        props = node._properties
        return labels,props
    
    with driver.session() as session:
        result = session.execute_read(get_nodes_and_rels)
    results= []
    for record in result:
        n = record["n"]
        r = record["r"]
        s = record["s"]

        source = format_node(n)
        target = format_node(s)
        d = {"source_labels":source[0], "source_props": source[1],"target_labels":target[0], "target_props":target[1], "relationship":r.type }
        results.append(d)
    return results

def format_triples(triples: list[dict]) -> str:
    def props_to_str(props):
        return "\n".join(f"  - {k}: {v}" for k, v in props.items() if v)
    formatted = []
    for i, triple in enumerate(triples, start=1):
        src_label = triple["source_labels"]
        src_props = triple["source_props"]
        rel = triple["relationship"]
        tgt_labels = triple["target_labels"]
        tgt_props = triple["target_props"]
        part = (
            f"Triple {i}:\n"
            f"{"".join(src_label)}:\n{props_to_str(src_props)}\n\n"
            f"Relationship: {rel}\n\n"
            f"{' / '.join(tgt_labels)}:\n{props_to_str(tgt_props)}\n"
            + "---"
        )
        formatted.append(part)
    return "\n\n".join(formatted)


def check_duplicate_nodes(node_type:str,prop_key:str, prop_val:str):
    query= """
    // Step 1: Find duplicates
    MATCH (n:{})
    WHERE n.{} = {}
    WITH collect(n) AS nodes, head(collect(n)) AS main
    """
    query.format(node_type, prop_key, prop_val)    


def merge_duplicate_nodes(driver, node_type,prop_key, prop_val):
    
    def _merge_duplicate_nodes(tx):
        query= """
        // Step 1: Find duplicates
        MATCH (n:{})
        WHERE n.{} = {}
        WITH collect(n) AS nodes, head(collect(n)) AS main

        // Step 2: Iterate over remaining nodes
        UNWIND nodes AS n
        WITH n, main
        WHERE id(n) <> id(main)

        // Step 3: Redirect incoming relationships
        CALL {{
        WITH n, main
        MATCH (m)-[r]->(n)
        CALL apoc.create.relationship(m, type(r), properties(r), main) YIELD rel
        DELETE r
        RETURN count(*) AS dummy1
        }}

        // Step 4: Redirect outgoing relationships
        CALL {{
        WITH n, main
        MATCH (n)-[r]->(m)
        CALL apoc.create.relationship(main, type(r), properties(r), m) YIELD rel
        DELETE r
        RETURN count(*) AS dummy2
        }}

        // Step 5: Merge properties if needed, delete duplicate
        WITH n, main
        SET main += n
        DELETE n
        """
        query.format(node_type,prop_key, prop_val)
    with driver.session() as session:
        session.run(_merge_duplicate_nodes)


def merge_by_id(driver, node_id1, node_id2):
    try:
        assert node_id1!=node_id2, "Both node ids are same"
    except AssertionError as e:
        return False
    
    def _match_node_labels(tx, node_id1, node_id2):
        query = """
            MATCH (n1) WHERE elementId(n1) = $node_id1
            MATCH (n2) WHERE elementId(n2) = $node_id2
            WITH n1, n2, labels(n1) = labels(n2) AS label_match
            RETURN label_match
        """
        return list(tx.run(query, node_id1 = node_id1, node_id2=node_id2))
        
    def _merge_by_id(tx, node_id1, node_id2):
        query = """
                MATCH (n1) WHERE elementId(n1) = $node_id1
                MATCH (n2) WHERE elementId(n2) = $node_id2
                
                // 🧠 Continue only if labels match
                CALL (n1, n2) {
                WITH n1, n2
                // Merge properties from n2 to n1 only if n1[prop] is null or empty
                UNWIND keys(n2) AS prop_key
                WITH n1, n2, prop_key
                WHERE n1[prop_key] IS NULL OR n1[prop_key] = ''
                CALL apoc.create.setProperty(n1, prop_key, n2[prop_key]) YIELD node
                RETURN count(*) AS props_merged
                }

                // 🔁 Rewire incoming relationships
                CALL(n1, n2) {
                WITH n1, n2
                MATCH (x)-[r]->(n2)
                CALL apoc.create.relationship(x, type(r), properties(r), n1) YIELD rel
                DELETE r
                RETURN count(*) AS in_relinked
                }

                // 🔁 Rewire outgoing relationships
                CALL(n1, n2) {
                WITH n1, n2
                MATCH (n2)-[r]->(x)
                CALL apoc.create.relationship(n1, type(r), properties(r), x) YIELD rel
                DELETE r
                RETURN count(*) AS out_relinked
                }

                // 🧹 Finally delete the duplicate
                WITH n1, n2
                DELETE n2
                RETURN elementId(n1) AS kept_node
        """
        return list(tx.run(query, node_id1 = node_id1, node_id2=node_id2))

    with driver.session() as session:
        res = session.execute_read(_match_node_labels, node_id1 = node_id1, node_id2 = node_id2)
    if res[0]["label_match"]:
        with driver.session() as session:
            session.execute_write(_merge_by_id, node_id1 = node_id1, node_id2 = node_id2)
        return True
    else:
        print("labels of nodes did not match!!")
        return False


def create_vector_index_for_node(driver, node, node_index,embedding_dim):
    def _create_vector_index_for_node(tx):
        query = f"""
        CREATE VECTOR INDEX {node_index} IF NOT EXISTS
        FOR (q:{node})
        ON q.embedding
        OPTIONS {{
            indexConfig: {{
                `vector.dimensions`: {embedding_dim},
                `vector.similarity_function`: 'cosine'
            }} 
        }}
        """
        tx.run(query)
    with driver.session() as session:
        session.execute_write(_create_vector_index_for_node)

def get_labels(tx):
    query = """
    CALL db.labels() YIELD label
    RETURN label
    ORDER BY label
    """
    return list(tx.run(query))
    

def create_vector_indices(driver, embedding_dim):
    with driver.session() as session:
        result = session.execute_read(get_labels)
        for record in result:
            create_vector_index_for_node(driver, record["label"], record["label"]+"_index",embedding_dim)


def get_node_property(driver, node:str)->dict:
    query = f"""
    MATCH (n:{node})
    WHERE NOT n:n4sch__Class AND NOT n:n4sch__Relationship AND NOT n:n4sch__Property
    RETURN n as node, properties(n) as property LIMIt 1
    """
    with driver.session() as session:
        prop = session.run(query).data()
    return prop


def create_node_embedding(driver,record, embedding_model, recreate_embedding:bool = False, vector_store:QdrantVectorStore=None):
    node_label = list(record.labels)[0]
    node_prop = list(record.keys())
    embedding_node_property = "embedding"
    if embedding_node_property in node_prop:
        node_prop.remove(embedding_node_property)
    def get_node_properties(tx, props):
        if recreate_embedding:
            fetch_query = f"""
                            MATCH (n)
                            WHERE elementId(n)='{record.element_id}'
                              AND n.{embedding_node_property} IS NOT null
                              AND any(k in $props WHERE n[k] IS NOT null)
                            RETURN elementId(n) AS id, n,
                            reduce(str = '', k IN $props |
                                CASE
                                  WHEN n[k] IS NOT null AND toString(n[k]) <> ''
                                  THEN str + '\\n' + k + ':' + toString(n[k])
                                  ELSE str
                                END
                            ) AS text
                            """
        else: 
            fetch_query = f"""
                            MATCH (n)
                            WHERE elementId(n)='{record.element_id}'
                              AND n.{embedding_node_property} IS null
                              AND any(k in $props WHERE n[k] IS NOT null)
                            RETURN elementId(n) AS id, n,
                            reduce(str = '', k IN $props |
                                CASE
                                  WHEN n[k] IS NOT null AND toString(n[k]) <> ''
                                  THEN str + '\\n' + k + ':' + toString(n[k])
                                  ELSE str
                                END
                            ) AS text
                            """
            
        return list(tx.run(fetch_query, props=props))

    def update_text_embedding(tx, data):
        query = f"""
                    UNWIND $data AS row
                    MATCH (n:`{node_label}`)
                    WHERE elementId(n) = row.id
                    CALL db.create.setNodeVectorProperty(n, '{embedding_node_property}', row.embedding)
                    RETURN count(*)
                """
        tx.run(query, data=data)


    with driver.session() as session:
        ds = session.execute_read(get_node_properties,node_prop)
    print(f"======= {ds}")
    if not ds:
        return
    if vector_store is None: # If vector DB instance is not provided then use the default neo4j instance to store embeddings
        text_embeddings = embedding_model.embed_documents(["node_labels:"+str(list(el["n"].labels))+"\n" + el["text"] for el in ds])
        params = {
                        "data": [
                            {"id": el["id"], "embedding": embedding}
                            for el, embedding in zip(ds, text_embeddings)
                        ]
                    }
        with driver.session() as session:
            ds = session.execute_write(update_text_embedding, data = params["data"])
        return
    
    try:
        vector_store.add_texts(texts = ["node_labels:"+str(list(el["n"].labels))+"\n" + el["text"] for el in ds], 
                        metadatas = [{"node_labels": list(ds[0]["n"].labels),"element_id": ds[0]["n"].element_id } ])
        
        query = """
            MATCH (n)
            WHERE elementId(n) = $element_id
            SET n.embedding = true
            RETURN n
            """
        with driver.session() as session:
            result = session.run(query, element_id=record.element_id)
    except Exception as e:
        print(f"==== vector creation failed ====")
        pass

def create_all_node_embeddings(driver, embedding_model, vector_store):
    query = """
        MATCH(n)-[r]-(m)
        WHERE NOT labels(n) = ["Resource","n4sch__Class"] 
        AND NOT labels(n) = ["Resource","n4sch__Relationship"] 
        AND NOT labels(n) = ["Resource","n4sch__Property"]  
        AND NOT labels(n) = ["Resource"] 
        AND NOT labels(n) = ["_GraphConfig"] 
        AND NOT labels(n) = ["_NsPrefDef"] 
        RETURN DISTINCT(n)
    """
    with driver.session() as session:
        result = session.run(query)
        for record in result:
            create_node_embedding(driver,record["n"],embedding_model,recreate_embedding = False, vector_store = vector_store)


def read_document(file_path:str):
    """
    Call to read a pdf and extract text as string from this pdf and return this text.
    """
    loader = PyPDFLoader(file_path)
    pages = []
    text = ""

    for page in loader.lazy_load():
        pages.append(page)
        text = text+"\n"+page.page_content    
    # doc =  Document(page_content=text, metadata={"source": "local"})
    return text

def chunk_pdf(doc:str)->list:
    """
    Call to split a whole body of text in multiple chunks with overlap and return a list.
    """
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=20)
    text_chunks = text_splitter.split_text(doc)
    return text_chunks

def read_chunk(text_chunks):
    for chunk in text_chunks:
        yield chunk
        

def extract_case_metadata(model,chunk)->Dict:
    case_metadata_parser = ListOfTriplesParser(NodeTriple)
    metadata_extract_template = ChatPromptTemplate(
	    messages = [("system", METADATA_EXTRACTION_PROMPT), ("user", "{text}")],
        partial_variables={"format_instructions": case_metadata_parser.get_format_instructions()}
    )
    meta_extraction_chain = metadata_extract_template | model
    case_metadata = meta_extraction_chain.invoke({"text":chunk})
    triples = case_metadata_parser.parse(case_metadata.content)
    return triples


if __name__ == "__main__":
    
    uri = "bolt://neo4j:7687"
    username = "neo4j"
    password = "admin@123"

    driver = GraphDatabase.driver(uri, auth=(username, password))
    with driver.session() as session:
        labels = session.execute_read(get_node_labels)
        print("Node Labels:", labels)
    
    with open("sample_response.json", "r") as file:
        jsondata = json.load(file)
    
    # test
    merged_node_with_label_and_prop("Judge")
        