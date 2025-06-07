Here’s a more casual and personal version of the README.md:

```markdown
# ITL.CloudInit

This is a personal project I’ve been working on to manage provisioning profiles and generate bootable ISO files for cloud-init-based systems. It’s built with FastAPI and SQLAlchemy, and it’s been a fun way to explore some cool tech like TPM validation and ISO generation.

---

## What’s Inside?

Here’s a quick overview of what this project does:

- **Provisioning Profiles**: Manage profiles for devices using MAC addresses or TPM attestation.
- **Metadata & User Data**: Serve cloud-init `meta-data` and `user-data` for provisioning.
- **ISO Generation**: Create bootable ISO files with cloud-init data baked in.
- **Pending Profiles**: Store unknown devices for manual approval later.

---

## How to Run It

---

## Endpoints

Here are the main endpoints you can play with:

### **1. Bootstrap a Device**
- **POST** `/bootstrap`
- **What it does**: Handles provisioning requests for devices.
- **Headers**: Add `X-MAC-Address` for MAC-based devices.
- **Body**:
  ```json
  {
    "serial_number": "string",
    "bios_vendor": "string",
    "bios_version": "string",
    "tpm": {
      "quote": "string",
      "nonce": "string",
      "aik_pub": "string",
      "expected_hash": "string"
    },
    "api_token": "string"
  }
  ```

### **2. Get Metadata**
- **GET** `/seed/{identifier}/meta-data`
- **What it does**: Returns the `meta-data` for a profile.

### **3. Get Cloud-Config**
- **GET** `/cloud-config/{identifier}`
- **What it does**: Returns the `user-data` for a profile.

### **4. Create a Bootable ISO**
- **POST** `/create-boot-iso`
- **What it does**: Generates a bootable ISO file for a profile.
- **Response**:
  ```json
  {
    "status": "ISO created",
    "path": "/tmp/{identifier}-seed.iso"
  }
  ```

---

## Security Stuff

This is just a personal project, but I’ve added some basic security features:
- **TPM Validation**: Verifies device integrity using TPM attestation.
- **API Tokens**: Makes sure only authorized devices can access profiles.
- **Temporary Files**: ISO files are stored in `/tmp`. Cleanup might be needed if you’re running this long-term.

---

## Notes

- This is still a work in progress, so there might be some rough edges.

---

## Why I Built This

I built this project to expand my knowledge of **cloud-init** and explore how it can be integrated with tools like the **Kubernetes autoscaler** for bare-metal environments. The idea is to create a custom API that adds extra layers of protection while provisioning fully unattended systems. 

The ultimate goal is to enable seamless scaling of worker nodes, deploying clusters, and managing infrastructure in a way that’s both secure and automated. It’s a fun challenge to combine cloud-init, Kubernetes, and custom APIs to build something that works reliably in bare-metal setups!

