import yaml
from neo4j import GraphDatabase

# Load config
with open('.config.yaml', 'r') as f:
    config = yaml.safe_load(f)

remote_config = config['neo4j']['remote']
uri = remote_config['uri']
user = remote_config['user']
password = remote_config['password']

print(f"Connecting to: {uri}")
print(f"User: {user}")

driver = GraphDatabase.driver(uri, auth=(user, password))
with driver.session() as session:
    # Check total nodes
    result = session.run('MATCH (n) RETURN count(n) as count')
    total_nodes = result.single()['count']
    print(f'Total nodes in database: {total_nodes}')
    
    # Check Server nodes
    result = session.run('MATCH (s:Server) RETURN count(s) as count')
    server_count = result.single()['count']
    print(f'Server nodes: {server_count}')
    
    # Check registry sources
    result = session.run('MATCH (s:Server) RETURN DISTINCT s.registry_source as source, count(s) as count ORDER BY count DESC')
    print(f'\nRegistry sources:')
    for record in result:
        source = record['source']
        count = record['count']
        print(f'  {source}: {count}')
    
    # Check a sample server
    result = session.run('MATCH (s:Server) RETURN s LIMIT 1')
    sample = result.single()
    if sample:
        server = sample['s']
        print(f'\nSample server:')
        print(f'  ID: {server.get("id")}')
        print(f'  Name: {server.get("name")}')
        print(f'  Registry source: {server.get("registry_source")}')
        print(f'  Categories: {server.get("categories")}')
        print(f'  Operations: {server.get("operations")}')
    
    # Check other node types
    result = session.run('MATCH (n) RETURN labels(n) as labels, count(n) as count')
    node_types = {}
    for record in result:
        labels = record['labels']
        count = record['count']
        if labels:
            label_str = ':'.join(labels)
            node_types[label_str] = count
    
    print(f'\nNode types in database:')
    for label, count in node_types.items():
        print(f'  {label}: {count}')

driver.close() 