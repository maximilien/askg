import yaml
from neo4j import GraphDatabase

# Load config
import os
config_path = os.path.join(os.path.dirname(__file__), '..', '.config.yaml')
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

# Use local config by default, fallback to remote if available
if 'local' in config['neo4j']:
    neo4j_config = config['neo4j']['local']
elif 'remote' in config['neo4j']:
    neo4j_config = config['neo4j']['remote']
else:
    raise ValueError("No Neo4j configuration found in config file")

uri = neo4j_config['uri']
user = neo4j_config['user']
password = neo4j_config['password']

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