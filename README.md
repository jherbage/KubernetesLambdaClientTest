# KubernetesLambdaClientTest
Smoke tests a K8 cluster using a python lambda function

The zip file has all the libs for python kubernetes client
The provided yaml and python script can spin up a nginx container on each worker node, test nginx can be contacted on a nodePort service.
Then updates the service to a new port, tests connectivity again and finally tears down the deployment and service readying the K8 cluster for business.

See my CF templates repository for an example template (k8testLambdaPopulateS3Bucket) which can make use of this repository in a wider K* cluster build as a smoke test at the end of the build.
