
# AI Commercial Real Estate Analyst - Deployment Guide

This guide provides clear, step-by-step instructions to deploy the application to a live server on Google Compute Engine (GCE).

## Deployment Strategy

We will use a modern, container-based approach for a reliable and repeatable deployment:
1.  **Google Compute Engine (GCE)**: We will create a virtual server (a "VM") in the Google Cloud to host our application.
2.  **Docker**: The frontend and backend are packaged into "containers". This ensures they run the same way on the server as they do on your local machine, avoiding environment-related bugs.
3.  **Docker Compose**: This tool manages our containers, making it easy to start, stop, and connect them.
4.  **Deployment Script (`deploy.sh`)**: A script that automates the final setup steps on the server.

## Prerequisites

Before you start, you must have:
-   A Google Cloud Platform (GCP) account with billing enabled.
-   Your application code pushed to a GitHub or GitLab repository. This is how you will get the code onto the server.

---

## Step 1: Prepare Your Google Cloud Environment

In this step, we will create and configure the virtual server.

### 1. Create the Virtual Machine (VM)

This will be the computer in the cloud that runs your application.

-   Go to the [Google Cloud Console](https://console.cloud.google.com/) and navigate to **Compute Engine** > **VM instances**.
-   Click **"CREATE INSTANCE"**.
-   **Name**: `cre-analyst-vm` (or a name of your choice).
-   **Region/Zone**: Choose one that is geographically close to you (e.g., `us-central1`).
-   **Machine configuration**:
    -   Series: `E2`
    -   Machine type: `e2-medium` (This is a good, cost-effective starting point).
-   **Boot disk**: This is the VM's operating system.
    -   Click **"Change"**.
    -   For **Operating system**, select `Container-Optimized OS`. This is a special version of Linux from Google that comes with Docker pre-installed, which is perfect for us.
    -   Click **"Select"**.
-   **Firewall**:
    -   Check the box for **"Allow HTTP traffic"**.
    -   Check the box for **"Allow HTTPS traffic"**.
-   Click the **"Create"** button at the bottom. Wait a minute or two for the VM to be created.

### 2. Reserve a Static IP Address

By default, the VM's public IP address can change if you stop and start it. We want a permanent, unchanging address.

-   In the Google Cloud Console, navigate to **VPC Network** > **IP Addresses**.
-   You will see a list of IP addresses. Find the one assigned to your new VM (`cre-analyst-vm`). Its "Type" will be **Ephemeral**.
-   Click on **"Ephemeral"**.
-   A new page will open. Give the static IP a **Name** (e.g., `cre-analyst-ip`) and click **"RESERVE"**.
-   **Important**: Copy this new static IP address. You will need it later.

### 3. Create a Firewall Rule for the Backend

Your VM can now receive web traffic on port 80 (standard HTTP). However, our backend API runs on port `8000`. We need to tell Google Cloud to allow traffic to this port.

-   In the Google Cloud Console, navigate to **VPC Network** > **Firewall**.
-   Click **"CREATE FIREWALL RULE"** at the top.
-   **Name**: `allow-backend-api-8000`.
-   **Targets**: Leave as `All instances in the network`.
-   **Source IPv4 ranges**: Enter `0.0.0.0/0`. This means "allow traffic from any IP address on the internet".
-   **Protocols and ports**:
    -   Select `Specified protocols and ports`.
    -   Check the `TCP` box.
    -   In the text field next to TCP, enter `8000`.
-   Click **"Create"**.

Your cloud environment is now fully prepared!

---

## Step 2: Deploy the Application Code

Now we will connect to the VM and run our application.

### 1. Connect to Your VM via SSH

-   Go back to the **Compute Engine** > **VM instances** page.
-   Find your `cre-analyst-vm` instance in the list.
-   On the right side, click the **"SSH"** button.
-   A new browser window will open, giving you a command-line terminal connected directly to your VM. All the following commands should be run in this SSH window.

### 2. Install Docker Compose

The VM has Docker, but we need to add Docker Compose. Run this command in the SSH terminal:
```bash
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose && sudo chmod +x /usr/local/bin/docker-compose
```
This downloads Docker Compose and makes it executable.

### 3. Clone Your Application from GitHub/GitLab

Use `git` to download your application code onto the VM.
```bash
# Replace the URL with your repository's URL
git clone https://github.com/your-username/your-repo-name.git

# Navigate into the project directory
cd your-repo-name
```

### 4. Configure the Backend Environment

Your backend needs the secret API keys to function. We will create the `.env` file on the server.

-   Navigate into the backend directory: `cd backend`
-   Use the `nano` text editor to create the file: `nano .env`
-   Type your secrets into the editor:
    ```
    API_KEY="YOUR_GOOGLE_API_KEY_HERE"
    GCP_PROJECT_ID="your-gcp-project-id-here"
    ```
-   Press `Ctrl+X` to exit, then `Y` to confirm you want to save, and finally `Enter` to save the file.

### 5. Run the Deployment Script

This is the final step. The `deploy.sh` script will automate the rest.

-   Go back to the project's root directory: `cd ..`
-   Make the deployment script executable: `chmod +x deploy.sh`
-   Run the script, passing your **static IP address** (that you copied earlier) as the one and only argument:
    ```bash
    # Replace with your actual static IP
    ./deploy.sh 34.123.45.67
    ```

The script will configure the frontend, then build and launch the Docker containers.

---

## Step 3: Access Your Live Application

You're done! Open your web browser and navigate to your server's static IP address:

**http://YOUR_STATIC_IP_ADDRESS_HERE**

The application should load, and the "Backend Online" indicator should be green. Your application is now live on the internet and ready to use.
