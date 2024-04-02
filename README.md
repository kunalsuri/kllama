# ✅🦙Kllama: Your Private Chatbot :dependabot:

⚡ Your personal & private chatbot running on open LLM model(s) ⚡

[![X (formerly Twitter) Follow](https://img.shields.io/twitter/follow/kunalsuri)](https://twitter.com/kunalsuri)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![GitHub language count](https://img.shields.io/github/languages/count/kunalsuri/kllama)
![GitHub top language](https://img.shields.io/github/languages/top/kunalsuri/kllama?color=yellow)
![GitHub Repo stars](https://img.shields.io/github/stars/kunalsuri/kllama)



<br>

> Author: Kunal Suri, Ph.D.
>
> Other Info: The symbol {✅🦙} for Kllama stands for OK, Llama (or) Kunal's llama! 😁🙏

<br>

## 🚀 How to use Kllama?
This application can be executed in two ways: (1) using open-source LLM models from the local machines, or (2) using open-source LLM models providers online by services such as Replicate.com or HuggingFace.com

### Table of Contents
1. [Prerequisites](#Prerequisites)
2. [Running Kllama Locally via CLI](#Running-Kllama-Locally-CLI)
3. [Running Kllama via Models Online](#Running-Kllama-Online)

<br>

---

### Prerequisites

To use the Kllama App, you need do the following steps:

1. **Download, Install and Run Ollama Application**

   > The Ollama framework enables easy interaction between your chatbot and the LLM models from the convenience of your local machine.
   
   Kindly, follow the instructions from [Ollama](https://ollama.com/) website to download and install the framework in your local machine. Once Ollama is installed, you can run a local open-source LLM model from your machine. The general steps are given below:

   > (For more details and info please check: [Ollama](https://ollama.com/))


   - Download and Install Ollama app (Supported Platforms: Windows, Linux, MacOS)
      
      - For Window Users: Once Ollama application is downloaded, you will need to run the Ollama app from Programs
      
      - Once the Ollama app is running, go to commant prompt (CLI) and type:
        
        ```bash
           Ollama list
        ```
        > Note: This command is used to list all the open-source LLM models available in your system locally. However, on the first run, then may be no LLM models in your system.

    
   - To download the LLM model, run the command
     >  Ollama run <Model_Name>
     
       ```bash
          Ollama run mistral
       ```
     
     > This command will check if the model is available in the local repo on your machine, if not then it will fetch the LLM model from Ollama Website and then start running it.

   
2. **Replicate the Git Repo in your local machine**

   > We assume that you have cloned the Kllama repo on your local machine. If not, do the following:

```bash
git clone https://github.com/kunalsuri/kllama.git
```

<br>

⚠️ Recommendation: To keep their python installations for other projects clean, we recommend that the users create a new python virtual environment for the Kllama project and install the python packages via requirement.txt (in Step 3 below)

<br>

3. **Install the python packages needed to run the Kllama Chatbot**

> Kllama.py application needs the following packages: ollama, streamlit. They have been included to the requirements.txt and can be easily installed. To install the packages, go to the folder containing Kllama and enter the below command:

```bash
pip install -r requirements.txt
```

<br>

---

### Running Kllama Locally via CLI
Kllama uses open-source LLM models running on your machine via the **Ollama** framework. To run these models, the user needs to install Ollama (as detailed in the Prerequisite section above). 

We assume that you have installed the Ollama framework and downloaded the open LLM models such as [Mistral](https://mistral.ai/technology/#models), or Meta's [Llama 2](https://llama.meta.com/), [Codelama](https://ai.meta.com/blog/code-llama-large-language-model-coding/), to name just a few.

> To run the Kllama via command-line interface (CLI) use the following command: 

```bash
streamlit run kllama.py
```

✅ Once executed, the Kllama Chatbot will start running on your web browser and will be ready for your use.

<br>

---

### Running Kllama via Models Online

> Running Kllama online needs the user to have an account in webservices such as Replicate.com to use the open LLM models running there.

<br>

⚠️ Note: We are not affiliated with [Replicate.com](https://replicate.com) company; I simply found their service interesting and decided to use it.

<br>

#### Prerequisites for using models online
1. Create an account in Replicate.com
2. Get the API token from your Replicate.com
3. Place the API token in the .streamlit/secrets.tom file
   > REPLICATE_API_TOKEN = "PUT YOUT TOKEN HERE"

<br>

#### Running Kllama via Models deployed Online
> To run the Kllama via command-line interface (CLI) first we need to install the replicate package via the following command:

replicate
```bash
pip install replicate
```

<br>

> Next, run the following command

```bash
streamlit run kllama_online.py
```
   
<br>

✅ Once configured and executed properly, the Kllama Chatbot will start running via the kllama-online.py app on your web browser and will be ready for your use.

For the Kllama (online version), the user can use the Llama2-7B model or Llama2-13B model that is available in the [Replicate.com](https://replicate.com) website. There are some trial credits available to the user and then the user may need to pay, based on the rules from Replicate.com.

<br>

---

## 🛡️Responsible AI 
:european_union: **EU's Guidelines on the responsible use of generative AI in research:** https://research-and-innovation.ec.europa.eu/news/all-research-and-innovation-news/guidelines-responsible-use-generative-ai-research-developed-european-research-area-forum-2024-03-20_en

<br>

⚠️ Note: In no circumstance shall the author(s) or copyright holder(s) be held liable for any claim, damages, or other liabilities arising from the utilization of this code, which incorporates several code snippets generated by artificial intelligence (AI), along with opne source contributions from other programmers sourced from GitHub and other platforms, pursuant to the terms outlined in the MIT License.



