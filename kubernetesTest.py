from kubernetes import client, config
from shutil import copyfile
import cfnresponse
import yaml
from os import path
import time

DEPLOYMENT_NAME = "nginx-deployment"

def create_deployment_object():
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
        replicas=3,
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
  if hasattr( event, 'RequestType') and event['RequestType'] == 'Create':
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
    deployment = create_deployment_object()

    create_deployment(extensions_v1beta1, deployment)

    update_deployment(extensions_v1beta1, deployment)
    time.sleep(20)
    ret = v1.list_pod_for_all_namespaces(watch=False)
    data=[]
    for i in ret.items:
      print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))
      data.append("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))

    delete_deployment(extensions_v1beta1)
	
    try:
      cfnresponse.send(event, context, cfnresponse.SUCCESS, "succeeded", {"data": " ".join(data)})
    except Exception as e:
      print "couldnt respond to stack create: "+str(e)
  elif hasattr( event, 'RequestType'):
    try:
      cfnresponse.send(event, context, cfnresponse.SUCCESS, "succeeded", {})
    except Exception as e:
      print "couldnt respond to stack delete: "+str(e)    