import docker, time
import logging

logging.basicConfig(filename="deploy.log", filemode='w', level=logging.DEBUG, format='%(asctime)s : %(name)s => %(levelname)s - %(message)s')

def spawnContainer(type_of_container, level_number, highest_level_of_deployment, container_number):
    client = docker.from_env()

    image_to_run = type_of_container
    container_name = type_of_container + str(container_number)
    
    if type_of_container == "load_balancer":
        container = client.containers.run(image=image_to_run, detach=True, network="blockchain", name=container_name, hostname=container_name, ports={'8080/tcp': 80}, environment=["CUSTOM_PORT=8080", "HIGHEST_LEVEL={}".format(highest_level_of_deployment)], volumes={'/var/run/docker.sock': {'bind': '/var/run/docker.sock', 'mode': 'rw'}, '/home/blockchain/logs/': {'bind': '/usr/src/app/logs', 'mode': 'rw'}})

    else:
        container = client.containers.run(image=image_to_run, detach=True, network="blockchain", name=container_name, hostname=container_name, environment=["CUSTOM_PORT=80", "CURRENT_LEVEL={}".format(level_number), "HIGHEST_LEVEL={}".format(highest_level_of_deployment)], volumes={'/var/run/docker.sock': {'bind': '/var/run/docker.sock', 'mode': 'rw'}, '/home/blockchain/logs/': {'bind': '/usr/src/app/logs', 'mode': 'rw'}})
    
    time.sleep(10)
    process = container.top()

    client.close()
    return int(process['Processes'][0][1])

if __name__ == '__main__':
    client = docker.from_env()
    network_list = client.networks.list()
    create_net = False
    
    for network in network_list:
        if network.name == "blockchain":
            create_net = True
    
    if create_net == False:
        client.networks.create("blockchain", driver="bridge")
    
    client.close()
    
    level_of_deployment = int(input("Please enter a number for the level of deployment (value starts from 1): "))
    highest_level_of_deployment = int(input("Enter the number of the highest level of deployment: "))
    
    number_of_nodes = int(input("Enter number of api nodes: "))
    number_of_orderers = int(input("Enter number of orderer nodes: "))

    for i in range(1, number_of_nodes + 1):
        pid = spawnContainer("bc", level_of_deployment, highest_level_of_deployment, i)
        logging.info("BC container {} started. Number of containers left {}".format(i, number_of_nodes - i))
        logging.debug("BC Container pid {}".format(pid))
    
    for i in range(1, number_of_orderers + 1):
        pid = spawnContainer("orderer", level_of_deployment, highest_level_of_deployment, i)
        logging.info("BC orderer container {} started. Number of containers left {}".format(i, number_of_orderers - i))
        logging.debug("BC orderer Container pid {}".format(pid))

    pid = spawnContainer("load_balancer", level_of_deployment, highest_level_of_deployment, 1)
    logging.info("Load Balancer container started. Container pid {}".format(pid))
    
    print("Done spawning the containers")