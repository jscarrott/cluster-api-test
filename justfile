

start_cluster:
    k3d cluster create -c k3dconfig.yaml

publish:
    pants publish ::

install_chart: publish
    pants package chart::
    helm upgrade --install api-test ./dist/chart.api-test/api-test/api-test-0.1.0.tgz
