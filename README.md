## Network and Computer Security | 1 Semester 2018/2019

* João Miguel Campos, 75785, MEIC-T
* Tiago Taveira, 77941, MEIC-T --> [@TiagoTaveira](https://github.com/TiagoTaveira)
* Vasco Pombo, 78029, MEIC-T --> [@vascopombo](https://github.com/vascopombo)

**Course:** Segurança Informática em Redes e Sistemas (SIRS) | Network and Computer Security

**Course Link:** https://fenix.tecnico.ulisboa.pt/disciplinas/SIRS/2018-2019/1-semestre

| Nome | Sprint Inicial | Sprint Intermédio | Sprint Final |
| -----| -------------- | --------------- | ----------- |
| João Miguel | Estrutura base - *Server* | Comunicação (*dispositivos - Server*) | Criptografia & Segurança |
| Tiago Taveira| Estrutura base - *Manager* | Comunicação (*dispositivos - Server*) | Criptografia & Segurança |
| Vasco Pombo | Estrutura base - *Tracker* | Comunicação (*dispositivos - Server*) | Criptografia & Segurança |



## Como gerar os certificados?
##### [Source and inspiration](https://www.itsfullofstars.de/2017/02/openssl-ca-to-sign-csr-with-sha256-sign-csr-issued-with-sha-1/)

>"When a CSR is created, a signature algorithm is used. Normally, this is SHA-1. Installing a TLS certificate that is using SHA-1 will give some problems, as SHA-1 is not considered secure enough by Google, Mozilla, and other vendors. Therefore, the final certificate needs to be signed using SHA-256. In case the CSR is only available with SHA-1, the CA can be used to sign CSR requests and enforce a different algorithm."




**1.** Para gerar os nossos certificados, começamos por [executar o comando:](https://stackoverflow.com/questions/10175812/how-to-create-a-self-signed-certificate-with-openssl#10176685)

```bash
openssl req -x509 -newkey rsa:2048 -keyout rootCAKey.pem -out rootCA.pem -days 365
```

Que gera um _self signed certificate_ com uma chave _RSA_ de 2048 bits e gera dois ficheiros, o _rootCAKey.pem_, que é a chave privada do certificado encriptada, e _rootCA.pem_ que é o certificado.

**2.** Depois, executar o comando:

 ```bash
 openssl req -out mainServer.csr -new -newkey rsa:2048 -nodes -keyout mainServer.key
 ```
* Aqui, são criados dois ficheiros, _mainServer.csr_, que é um _Certificate Signing Request_, ou seja, é um pedaço de texto encriptado que é dado a uma Entidade Certificadora para que esta possa certificar a entidade que faz o pedido, e a sua chave privada, _mainServer.key_.

**3.** Agora verifica-se o algoritmo de assinatura de _mainServer.csr_.

```bash
openssl req -verify -in mainServer.csr -text -noout
```

**4.** Com este comando, a _Certifying Authority_ assina o _Certificate Signing Request_ utilizando o algoritmo _SHA-256_. Assim, é geradao o certificado _mainServer.crt_.

```bash
openssl x509 -req -days 360 -in mainServer.csr -CA rootCA.pem -CAkey rootCAKey.pem -CAcreateserial -out mainServer.crt -sha256
```


**5.** Com este último comando apenas estamos a verificar que realmente o certificado ficou assinado com o algoritmo _SHA-256_.

```bash
openssl x509 -text -noout -in mainServer.crt
```



Para conseguir o certificado para o KDC, basta executar desde o passo _**2.**_ e trocar o nome _**mainServer**_ por _**KDC**_.

## Para executar o código

Basta correr o código em _Python3.6_, da seguinte maneira:

```bash
./Server.py
```
```bash
./KDC.py
```
```bash
./ManagerApp.py
```
```bash
./TrackerApp.py
```



**Disclaimer:**
This repository, and every other ist_COURSE repos on GitHub correspond to school projects from the respective COURSE. The code on this repo is intended for educational purposes. I do not take any responsibility nor liability over any code faults, inconsistency or anything else. If you intend on copying most or parts of the code for your school projects, keep in mind that this repo is public, and that your professor might search the web for similar project solutions and choose to fail you for copying.


## Have fun coding! :)
