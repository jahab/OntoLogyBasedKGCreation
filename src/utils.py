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



if __name__ == "__main__":
    
    uri = "bolt://localhost:7687"
    username = "neo4j"
    password = "admin@123"

    driver = GraphDatabase.driver(uri, auth=(username, password))
    with driver.session() as session:
        labels = session.execute_read(get_node_labels)
        print("Node Labels:", labels)