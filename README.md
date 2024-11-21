# heirloom-project
Implement the Systems and Reliability Engineer - Technical Exercise

# How to deploy

Assumes a k8s cluster already exists.
Install the helm dependancies:

    1.  install helm (brew instal helm)
    2.  helm repo add bitnami https://charts.bitnami.com/bitnami
    3.  helm repo update

Swap the credentials in values.yaml for something secure.

Deploy the helm chart to your cluster
`helm install mysql bitnami/mysql -f values.yaml`

## Diagram for High Availability MySQL Server
```mermaid
flowchart TB
    subgraph "Kubernetes Cluster"
        subgraph "Node 1"
            mysql1["MySQL Pod 1<br>(Primary)"]
            pv1["Persistent Volume 1"]
            mysql1 --- pv1
        end
        subgraph "Node 2"
            mysql2["MySQL Pod 2<br>(Secondary)"]
            pv2["Persistent Volume 2"]
            mysql2 --- pv2
        end
        subgraph "Node 3"
            mysql3["MySQL Pod 3<br>(Secondary)"]
            pv3["Persistent Volume 3"]
            mysql3 --- pv3
        end

        svc["MySQL Service<br>(LoadBalancer)"]
        svc --> mysql1
        svc --> mysql2
        svc --> mysql3

        cronjob["Backup CronJob"]
    end

    app["Application Pods"] --> svc

    subgraph "External Services"
        s3["AWS S3<br>Backup Bucket"]
    end

    cronjob --> s3
```

## Diagram for Single Node Failover Scenario
```mermaid
flowchart TB
    subgraph "Kubernetes Cluster"
        subgraph "Control Plane"
            orchestrator["MySQL Orchestrator<br>Pod"]
        end

        subgraph "Node 1"
            mysql1["MySQL Pod 1<br>(Primary)"]
            pv1["Persistent Volume 1"]
            mysql1 --- pv1
        end
        subgraph "Node 2"
            mysql2["MySQL Pod 2<br>(Secondary)"]
            pv2["Persistent Volume 2"]
            mysql2 --- pv2
        end
        subgraph "Node 3"
            mysql3["MySQL Pod 3<br>(Secondary)"]
            pv3["Persistent Volume 3"]
            mysql3 --- pv3
        end

        orchestrator --> mysql1
        orchestrator --> mysql2
        orchestrator --> mysql3

        svc["MySQL Service<br>(LoadBalancer)"]
        svc -.-> orchestrator

        mysql1 --> mysql2
        mysql1 --> mysql3
    end

    app["Application Pods"] --> svc

    classDef failure fill:#ff6666,stroke:#333,stroke-width:2px
    class mysql1 failure

    subgraph "Failover Scenario"
        direction TB
        step1["1. Primary fails"] --> step2["2. Orchestrator<br>detects failure"]
        step2 --> step3["3. Select new Primary<br>from secondaries"]
        step3 --> step4["4. Update replication"]
        step4 --> step5["5. Update Service<br>endpoints"]
        step5 --> step6["6. Raise Notification that primary node failed"]
    end
```