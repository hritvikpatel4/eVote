import docker, time
import logging

logging.basicConfig(filename="deploy.log", filemode='w', level=logging.DEBUG, format='%(asctime)s : %(name)s => %(levelname)s - %(message)s')

def spawnContainer(type_of_container, orderer_flag, container_number):
    client = docker.from_env()

    image_to_run = type_of_container
    container_name = type_of_container + str(container_number)
    
    if orderer_flag == True:
        image_to_run += "_orderer"
        container_name = "orderer" + str(container_number)
    
    if type_of_container == "load_balancer":
        container = client.containers.run(image=image_to_run, detach=True, network="blockchain", name=container_name, hostname=container_name, ports={'8080/tcp': 80}, environment=["CUSTOM_PORT=8080"], volumes={'/var/run/docker.sock': {'bind': '/var/run/docker.sock', 'mode': 'rw'}, '/home/$HOME/logs/': {'bind': '/usr/src/app/logs', 'mode': 'rw'}})

    else:
        container = client.containers.run(image=image_to_run, detach=True, network="blockchain", name=container_name, hostname=container_name, environment=["CUSTOM_PORT=80"], volumes={'/var/run/docker.sock': {'bind': '/var/run/docker.sock', 'mode': 'rw'}, '/home/$HOME/logs/': {'bind': '/usr/src/app/logs', 'mode': 'rw'}})
    
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
    
    type_of_deployment = input("Is it LBC or HBC deployment? (values to enter 'lbc' or 'hbc'): ")

    if type_of_deployment.lower() == "lbc":
        number_of_lbc = int(input("Enter the number of LBC nodes: "))
        number_of_lbc_orderer = int(input("Enter the number of LBC Orderer nodes: "))
        
        for i in range(1, number_of_lbc + 1):
            pid = spawnContainer("lbc", False, i)
            logging.info("LBC container {} started. Number of containers left {}".format(i, number_of_lbc - i))
            logging.debug("Container pid {}".format(pid))
        
        for i in range(1, number_of_lbc_orderer + 1):
            pid = spawnContainer("lbc", True, i)
            logging.info("LBC Orderer container {} started. Number of containers left {}".format(i, number_of_lbc_orderer - i))
            logging.debug("Container pid {}".format(pid))
        
        pid = spawnContainer("load_balancer", False, 1)
        logging.info("Load Balancer container started. Container pid {}".format(pid))
    
    elif type_of_deployment.lower() == "hbc":
        number_of_hbc = int(input("Enter the number of HBC nodes: "))
        number_of_hbc_orderer = int(input("Enter the number of HBC Orderer nodes: "))
        
        for i in range(1, number_of_hbc + 1):
            pid = spawnContainer("hbc", False, i)
            logging.info("HBC container {} started. Number of containers left {}".format(i, number_of_hbc - i))
            logging.debug("Container pid {}".format(pid))
        
        for i in range(1, number_of_hbc_orderer + 1):
            pid = spawnContainer("hbc", True, i)
            logging.info("HBC Orderer container {} started. Number of containers left {}".format(i, number_of_hbc_orderer - i))
            logging.debug("Container pid {}".format(pid))
        
        pid = spawnContainer("load_balancer", False, 1)
        logging.info("Load Balancer container started. Container pid {}".format(pid))
    
    else:
        pass