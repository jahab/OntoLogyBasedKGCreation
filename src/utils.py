import pandas as pd
import os
from neo4j import GraphDatabase
import json


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
    MATCH (n1:n4sch__Class {n4sch__name: $node1})-[]-(r:n4sch__Relationship {n4sch__name:$relationship})-[]-(n2:n4sch__Class {n4sch__name:$node2})
    RETURN n1,r,n2
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
    print(f"[{refine_parent_child_relation.__name__}]",node1_type, node2_type)
    invalid_node = True
    with driver.session() as session:
        subclasses_nodes = session.execute_read(find_subclass, node1_type) 
    # print(subclasses_nodes)
    for sc in subclasses_nodes:
        if (node1_type == sc['child'] and node2_type == sc['parent']):
            # print(sc['child'], sc['parent'])
            print("=========relation_correct")
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



def make_correct_pairs(jsondata):
    for json in jsondata:
        for item in json:
            node1_type = item["node1_type"]
            node2_type = item["node2_type"]
            node1_value = item["node1_value"]
            node2_value = item["node2_value"]
            relationship = item["relationship"]
            invalid_relation = False
            if relationship == "is_a":
                # Check if the extracted node is a valid subclass or not
                node1_type, node2_type, node1_value, node2_value,invalid_node = refine_parent_child_relation(node1_type,node2_type,node1_value,node2_value,relationship)
                if invalid_node ==  True:
                    print("Invalid Node relationship in subclass:", node1_type, relationship, node2_type)
                    print("====================")
                    continue
            
            # check if a valid relationship exists in ontology for between these node types
            with driver.session() as session:
                #first check for the valid relationship between node1 and the relationship itself
                edges = session.execute_read(check_valid_relationship, node1_type, relationship)
                print("Check for: ", node1_type,relationship,node2_type)
                if len(edges)==0: #if relationship doesnot exist then check for parent-child relationship of the node
                    print("Relation Not Found.. Checking for subclasses")
                    subclasses_nodes = session.execute_read(find_subclass, node1_type)
                    #check if Parent or child has a valid relation 
                    print(subclasses_nodes)
                    if len(subclasses_nodes)>0:
                        for node in subclasses_nodes:
                            print("******", node['child'], node['parent'])
                            sc_nodes = session.execute_read(check_valid_relationship,node['child'],relationship)
                            for e in sc_nodes:
                                # If valid connection is found the replace node with proper node
                                print("^^^--",e["p"]["n4sch__name"], e["o"]["n4sch__name"])
                                node1_type = e["p"]["n4sch__name"]
                            sc_nodes = session.execute_read(check_valid_relationship,node['parent'],relationship)
                            for e in sc_nodes:
                                print("--^^^",e["p"]["n4sch__name"], e["o"]["n4sch__name"])
                                node1_type = e["p"]["n4sch__name"]
                        invalid_relation = False
                    else:
                        invalid_relation = True


                edges = session.execute_read(check_valid_relationship,node2_type,relationship)
                print("Check for: ", node1_type,relationship,node2_type)
                if len(edges)==0: #if relationship doesnot exist then check for parent-child relationship of the node
                    print("Relation Not Found.. Checking for subclasses")
                    subclasses_nodes = session.execute_read(find_subclass, node2_type)
                    #check if Parent or child has a valid relation 
                    print(subclasses_nodes)
                    if len(subclasses_nodes)>0:
                        for node in subclasses_nodes:
                            print("******", node['child'], node['parent'])
                            sc_nodes = session.execute_read(check_valid_relationship,node['child'],relationship)
                            for e in sc_nodes:
                                # If valid connection is found the replace node with proper node
                                print("^^^--",e["p"]["n4sch__name"], e["o"]["n4sch__name"])
                                node2_type = e["p"]["n4sch__name"]
                            sc_nodes = session.execute_read(check_valid_relationship,node['parent'],relationship)
                            for e in sc_nodes:
                                print("--^^^",e["p"]["n4sch__name"], e["o"]["n4sch__name"])
                                node2_type = e["p"]["n4sch__name"]
                        invalid_relation = False
                    else:
                        invalid_relation = True
                # for e in edges:
                #     print(e["p"]["n4sch__name"], e["o"]["n4sch__name"])
                if invalid_relation == False:
                    
                    print(node1_type, node1_value, f"--[{relationship}]-->", node2_type, node2_value)
                    print("====================")


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

def get_single_node(tx, label):
    query = """
    MATCH (n:{}) RETURN n;
    """
    result = tx.run(query.format(label))
    return [r["n"] for r in result]  # List of lists



def merge_node(tx, labels, value):
    # Handle single or multiple labels
    label_str = ":" + ":".join(labels) if isinstance(labels, list) else f":{labels}"
    label = labels[0] if isinstance(labels, list) else labels

    # Step 1: Check for node key constraint
    constrained_keys_list = get_constraints_for_label(tx, label)
    print(constrained_keys_list)
    if constrained_keys_list:
        d = get_single_node(tx, label)
        if d:
            for key, val in d[0].items():
                if val:
                    constrained_keys_list[0].append(key)
        print("------",constrained_keys_list)
        constrained_keys_list[0] = list(set(constrained_keys_list[0]))
    # constrained_keys_list = constrained_keys_list
    # Step 2: Choose a constraint if available
    constrained_keys = None
    for keys in constrained_keys_list:
        if all(k in value for k in keys):  # Only use if all keys are available in the data
            constrained_keys = keys
            break

    print(constrained_keys)
    if constrained_keys:
        # Use only constraint keys in MERGE
        merge_props = ", ".join(f"{k}: ${k}" for k in constrained_keys)
        query = f"MERGE (n{label_str} {{ {merge_props} }})"

        # Now SET all the other properties (excluding merge keys)
        set_props = [k for k in value if k not in constrained_keys]
        if set_props:
            set_clause = ", ".join(f"n.{k} = ${k}" for k in set_props)
            query += f"\nSET {set_clause}"

        print(f"[{merge_node}] : using constraint keys: {constrained_keys}")
        tx.run(query, **value)

    else:
        # No constraints — fallback to using all props
        props = ", ".join(f"{k}: ${k}" for k in value)
        query = f"MERGE (n{label_str} {{ {props} }})"
        print(f"[{merge_node}] : no constraints, merging on all props")
        tx.run(query, **value)

def merge_relationship(tx, node1_type, node1_value, node2_type, node2_value, relationship):
    def format_labels(label):
        return ":" + ":".join(label) if isinstance(label, list) else f":{label}"

    node1_label_str = format_labels(node1_type)
    node2_label_str = format_labels(node2_type)

    # Build node1 match
    node1_params = {}
    if isinstance(node1_value, dict):
        node1_match = " AND ".join(f"n1.{k} = ${k}1" for k in node1_value)
        for k, v in node1_value.items():
            node1_params[f"{k}1"] = v
    else:
        key = f"{node1_type[-1].lower()}Name" if isinstance(node1_type, list) else f"{node1_type.lower()}Name"
        node1_match = f"n1.{key} = $node1_value"
        node1_params["node1_value"] = node1_value

    # Build node2 match
    node2_params = {}
    if isinstance(node2_value, dict):
        node2_match = " AND ".join(f"n2.{k} = ${k}2" for k in node2_value)
        for k, v in node2_value.items():
            node2_params[f"{k}2"] = v
    else:
        key = f"{node2_type[-1].lower()}Name" if isinstance(node2_type, list) else f"{node2_type.lower()}Name"
        node2_match = f"n2.{key} = $node2_value"
        node2_params["node2_value"] = node2_value

    # Combine WHERE clause safely
    where_clauses = []
    if node1_match:
        where_clauses.append(node1_match)
    if node2_match:
        where_clauses.append(node2_match)

    where_clause = " AND ".join(where_clauses)

    query = f"""
    MATCH (n1{node1_label_str}), (n2{node2_label_str})
    WHERE {where_clause}
    MERGE (n1)-[r:{relationship}]->(n2)
    """

    # Merge all parameters
    params = {**node1_params, **node2_params}

    print("Query:\n", query)
    print("Params:", params)

    tx.run(query, **params)


def merged_node_with_label_and_prop(driver, node:str):
    # find subclass and superclass  and properties for the given node
    print("Received_node",node)
    node_dict = {"properties":{}, "labels": [node]}
    parent_node = None
    with driver.session() as session:
        # while True:
        for _ in range(10):
            subclass_nodes = session.execute_read(find_subclass, node)
            # print(subclass_nodes)
            if (len(subclass_nodes)>0):
                for sc_node in subclass_nodes:
                    if sc_node["parent"] != node:
                        if sc_node["parent"] not in node_dict["labels"]:
                            node_dict["labels"].append(sc_node["parent"])
                        props = session.execute_read(find_property, sc_node["parent"])
                        if len(props)>0:
                            prop_dict = {}
                            for prop in props:
                                prop_dict[prop["property"]] = ""
                            node_dict["properties"] = prop_dict
                            # break
                        else: #if no property is found then traverse to more depth
                            node = sc_node["parent"]
                            # break
                    else:
                        props = session.execute_read(find_property,node)
                        if len(props)>0:
                            prop_dict = {}
                            for prop in props:
                                prop_dict[prop["property"]] = ""
                            node_dict["properties"] = prop_dict    
            else:
                props = session.execute_read(find_property,node)
                if len(props)>0:
                    prop_dict = {}
                    for prop in props:
                        prop_dict[prop["property"]] = ""
                    node_dict["properties"] = prop_dict
                    break
                
    return node_dict




def some_func_v2(driver, prop_ex_chain, node1_type, node1_value, relationship, node2_type,  node2_value):
    invalid_relation = False
    if relationship == "is_a":
        # Check if the extracted node is a valid subclass or not. If not then return with valid sublassing
        node1_type, node2_type, node1_value, node2_value,invalid_node = refine_parent_child_relation(driver, node1_type,node2_type,node1_value,node2_value,relationship)
        if invalid_node ==  True:
            print("Invalid Node relationship in subclass:", node1_type, relationship, node2_type)
            print("====================")
            return
    node1_dict = merged_node_with_label_and_prop(driver, node1_type) # {'properties': {'COLastName': '', 'COFirstName': ''},'labels': ['Judge', 'Court_Official']}
    node2_dict = merged_node_with_label_and_prop(driver, node2_type)
    # check if a valid relationship exists in ontology for between these node types
    print("[some_func_v2]\n", node1_dict, "\n",node2_dict)
    for label_1 in node1_dict['labels']:
        for label_2 in node2_dict['labels']:
            with driver.session() as session:
                edges = session.execute_read(check_valid_relationship, label_1, relationship, label_2) 
                for e in edges:
                    print("--^^^",e["n1"]["n4sch__name"],node1_dict["properties"], e["r"]["n4sch__name"], e["n2"]["n4sch__name"], node2_dict["properties"])

                    dc = prop_ex_chain.invoke({"node1_type": node1_type, "node2_type": node2_type,
                                       "relationship":relationship, 
                                       "node1_value":node1_value, "node2_value":node2_value,
                                       "node1_property":node1_dict["properties"], "node2_property":node2_dict["properties"],
                                       })
                    
                    return {"node1_dict":node1_dict,"node2_dict":node2_dict, "model_output":dc}
                    




def get_nodes_and_rels(tx):
    query = """
    MATCH p = (n)-[r]-(s)
    WHERE NOT n:n4sch__Class AND NOT n:n4sch__Relationship AND NOT n:n4sch__Property AND NOT n:Paragraph
    AND NOT s:n4sch__Class AND NOT s:n4sch__Relationship AND NOT s:n4sch__Property AND NOT s:Paragraph
    return n,r,s
    """
    return list(tx.run(query)) 


def get_graph(driver):

    with driver.session() as session:
        result = session.execute_read(get_nodes_and_rels)

    results= []
    for record in result:
        n = record["n"]
        r = record["r"]
        s = record["s"]

        def format_node(node):
            labels = ":".join(node.labels)
            props = node._properties
            return f"(:{labels} {props})"

        rel = f"-[:{r.type}]->" if r.start_node.id == n.id else f"<-[:{r.type}]-"
        results.append(f"{format_node(n)}{rel}{format_node(s)}")
    return results




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

def create_vector_indices(driver, embedding_dim):
    query = """
    CALL db.labels() YIELD label
    RETURN label
    ORDER BY label
    """
    with driver.session() as session:
        result = session.run(query)
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

def create_node_embedding(driver,node_label:str, embedding_model, recreate_embedding:bool = False):
    node_prop = get_node_property(driver, node_label)
    if node_prop:
        node_prop = list(node_prop[0]["node"].keys())
    
    
    embedding_node_property = "embedding"
    def get_node_properties(tx, props):
        if recreate_embedding:
            fetch_query = (
                f"MATCH (n:`{node_label}`) "
                f"WHERE n.{embedding_node_property} IS NOT null "
                "AND any(k in $props WHERE n[k] IS NOT null) "
                f"RETURN elementId(n) AS id, " 
                "reduce(str = '', k IN $props | "
                "CASE WHEN n[k] IS NOT null AND toString(n[k]) <> '' "
                "THEN str + '\\n' + k + ':' + toString(n[k]) "
                "ELSE str END) AS text "
                )
        else: 
            fetch_query = (
                f"MATCH (n:`{node_label}`) "
                f"WHERE n.{embedding_node_property} IS null "
                "AND any(k in $props WHERE n[k] IS NOT null) "
                f"RETURN elementId(n) AS id, " 
                "reduce(str = '', k IN $props | "
                "CASE WHEN n[k] IS NOT null AND toString(n[k]) <> '' "
                "THEN str + '\\n' + k + ':' + toString(n[k]) "
                "ELSE str END) AS text "
                )
            
        return list(tx.run(fetch_query, props=props))

    def update_text_embedding(tx, data):
        query = (
                    "UNWIND $data AS row "
                    f"MATCH (n:`{node_label}`) "
                    "WHERE elementId(n) = row.id "
                    f"CALL db.create.setNodeVectorProperty(n, "
                    f"'{embedding_node_property}', row.embedding) "
                    "RETURN count(*)"
                )
        tx.run(query, data=data)


    with driver.session() as session:
        ds = session.execute_read(get_node_properties,node_prop)
    text_embeddings = embedding_model.embed_documents([el["text"] for el in ds])
    params = {
                    "data": [
                        {"id": el["id"], "embedding": embedding}
                        for el, embedding in zip(ds, text_embeddings)
                    ]
                }

    with driver.session() as session:
        ds = session.execute_write(update_text_embedding, data = params["data"])


def create_all_node_embeddings(driver, embedding_model):
    query = """
    CALL db.labels() YIELD label
    RETURN label
    ORDER BY label
    """
    with driver.session() as session:
        result = session.run(query)
        for record in result:
            create_node_embedding(driver,record["label"], embedding_model)



if __name__ == "__main__":
    
    uri = "bolt://localhost:7687"
    username = "neo4j"
    password = "admin@123"

    driver = GraphDatabase.driver(uri, auth=(username, password))
    with driver.session() as session:
        labels = session.execute_read(get_node_labels)
        print("Node Labels:", labels)
    
    with open("sample_response.json", "r") as file:
        jsondata = json.load(file)
    
    # test
    make_correct_pairs(jsondata["Data"])
    # Test
    merged_node_with_label_and_prop("Judge")
        