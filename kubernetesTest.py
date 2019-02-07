from kubernetes import client, config

def handler(event,context):
  # Check the cert paths are relative to the working folder
  f1 = open('config', 'r')
  f2 = open('config-updated', 'w')
  for line in f1:
    f2.write(line.replace('/certs/', ''))
  f1.close()
  f2.close()
  # Configs can be set in Configuration class directly or using helper utility
  config.load_kube_config('config-updated')

  v1 = client.CoreV1Api()
  print("Listing pods with their IPs:")
  ret = v1.list_pod_for_all_namespaces(watch=False)
  for i in ret.items:
    print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))