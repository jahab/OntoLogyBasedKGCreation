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
        CREATE CONSTRAINT n10s_unique_uri ON (r:Resource)
        ASSERT r.uri IS UNIQUE;
        CALL n10s.onto.import.fetch("https://pastebin.com/raw/uYgpUDRr","Turtle"); 
    """
    tx.run(query)


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

    header =  "| Node1     | Relationship | Node2  | Comment                                                |"
    divider = "|-----------|--------------|--------|--------------------------------------------------------|"
    markdown_table = "\n".join([header, divider] + rows)
    print(markdown_table)

def format_properties_in_md(allowed_properties:list)->list:
    rows = []
    for index, (n1, rel, n2) in enumerate(allowed_properties):
        if comment == None:
            comment = ""    
        rows.append(f"| {n1:<10} | {rel:<12} | {n2:<6}    |")

    header =  "| Node1     | Property     | DataType                      |"
    divider = "|-----------|--------------|-----------|-------------------|"
    markdown_table = "\n".join([header, divider] + rows)
    print(markdown_table)



def check_valid_relationship(tx, node1, relationship):
    """
    Take a node and relationship as input and return if node and relationship exist or not
    If True tx.run will return two nodes
    If Flase tx.run will return empty list
    """
    query = """
    MATCH (p:n4sch__Class {n4sch__name: $node1})<-[]->(o:n4sch__Relationship {n4sch__name:$relationship})
    RETURN p,o
    """
    return list(tx.run(query,node1 = node1,relationship=relationship))

def refine_parent_child_relation(node1_type, node2_type, node1_val, node2_val, relationship):
    # print("Relation Not Found.. Checking for subclasses")
    print(node1_type, node2_type)
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
    #Now check if the node1 and Node2 are interchanges or not?  



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
    
    make_correct_pairs(jsondata["Data"])

        