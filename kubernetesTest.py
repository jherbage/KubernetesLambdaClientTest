from kubernetes import client, config
from shutil import copyfile
import cfnresponse
import yaml
from os import path
import time
import json
import boto3

DEPLOYMENT_NAME = "nginx-deployment"

def create_deployment_object(numberOfWorkerNodes):
  # Configureate Pod template container
  container = client.V1Container(
        name="nginx",
        image="nginx:1.7.9",
        ports=[client.V1ContainerPort(container_port=80)])
  # Create and configurate a spec section
  template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"app": "nginx"}),
        spec=client.V1PodSpec(containers=[container]))
  # Create the specification of deployment
  spec = client.ExtensionsV1beta1DeploymentSpec(
        replicas=numberOfWorkerNodes,
        template=template)
  # Instantiate the deployment object
  deployment = client.ExtensionsV1beta1Deployment(
        api_version="extensions/v1beta1",
        kind="Deployment",
        metadata=client.V1ObjectMeta(name=DEPLOYMENT_NAME),
        spec=spec)

  return deployment


def create_deployment(api_instance, deployment):
  # Create deployement
  api_response = api_instance.create_namespaced_deployment(
    body=deployment,
    namespace="default")
  print("Deployment created. status='%s'" % str(api_response.status))


def update_deployment(api_instance, deployment):
  # Update container image
  deployment.spec.template.spec.containers[0].image = "nginx:1.9.1"
  # Update the deployment
  api_response = api_instance.patch_namespaced_deployment(
    name=DEPLOYMENT_NAME,
    namespace="default",
    body=deployment)
  print("Deployment updated. status='%s'" % str(api_response.status))


def delete_deployment(api_instance):
  # Delete deployment
  api_response = api_instance.delete_namespaced_deployment(
    name=DEPLOYMENT_NAME,
    namespace="default",
    body=client.V1DeleteOptions(
      propagation_policy='Foreground',
      grace_period_seconds=5))
  print("Deployment deleted. status='%s'" % str(api_response.status))
	
def handler(event,context):

  # Only bother when creating or updating the stack
  if 'RequestType' in event and ( event['RequestType'] == 'Create' or event['RequestType'] == 'Update') :
    # Get number of worker nodes
    WorkerASGName = event['ResourceProperties']['WorkerASG']
    asg_client = boto3.client('autoscaling', region_name=event['ResourceProperties']['Region'])
  
    asg_response = asg_client.describe_auto_scaling_groups(AutoScalingGroupNames=[WorkerASGName])

    instance_ids = [] # List to hold the instance-ids

    for i in asg_response['AutoScalingGroups']:
      for k in i['Instances']:
        instance_ids.append(k['InstanceId'])

    ec2_response = ec2_client.describe_instances(
         InstanceIds = instance_ids
         )   
    print instance_ids #This line will print the instance_ids

    private_ip = [] # List to hold the Private IP Address

    for instances in ec2_response['Reservations']:
       for ip in instances['Instances']:
         private_ip.append(ip['PrivateIpAddress'])
    numberOfWorkerNodes=len(private_ip)
  
    print json.dumps(private_ip)

    # Check the cert paths are relative to the working folder
    f1 = open('config', 'r')
    f2 = open('/tmp/config-updated', 'w')
    for line in f1:
      f2.write(line.replace('/certs/', ''))
    f1.close()
    f2.close()
    copyfile('admin.pem', '/tmp/admin.pem')
    copyfile('admin-key.pem', '/tmp/admin-key.pem')
    # Configs can be set in Configuration class directly or using helper utility
    config.load_kube_config('/tmp/config-updated')

    v1 = client.CoreV1Api()
    #print("Listing pods with their IPs:")

    extensions_v1beta1 = client.ExtensionsV1beta1Api()
    deployment = create_deployment_object(numberOfWorkerNodes)

    create_deployment(extensions_v1beta1, deployment)

    update_deployment(extensions_v1beta1, deployment)
    time.sleep(20)
    ret = v1.list_pod_for_all_namespaces(watch=False)
    data=[]
    for i in ret.items:
      print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))
      data.append("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))
	
    # Test we can reach the port of nginx on the worker node it is deployed to
	## Get the IP addresses of the worker nodes
	
	
    delete_deployment(extensions_v1beta1)
	
    if 'StackId' in event:
      cfnresponse.send(event, context, cfnresponse.SUCCESS, "succeeded", {"data": " ".join(data)})
  elif 'RequestType' in event:
    if 'StackId' in event:
      cfnresponse.send(event, context, cfnresponse.SUCCESS, "succeeded", {})