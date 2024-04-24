# ✅🦙Kllama: Your Local & Private Chatbot :dependabot:

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
This application will can be executed on your local machine using open-source LLM models via the Ollama framework

### Table of Contents
1. [Prerequisites](#Prerequisites)
2. [Running Kllama Locally via CLI](#Running-Kllama-Locally-CLI)

<br>

---

### Prerequisites

The Kllama App runs on your local machine via Ollama framework. To use this app, you need do the following steps:

1. **Download, Install and Run Ollama Application**

   > The Ollama framework enables easy interaction between your chatbot and the LLM models from the convenience of your local machine.
   
   Kindly, follow the instructions from [Ollama](https://ollama.com/) website to download and install the framework in your local machine. Once Ollama is installed, you can run a local open-source LLM model from your machine. The general steps are given below:

   > (For more details and info please check: website: [Ollama](https://ollama.com/)) || **GitHub:** https://github.com/ollama/ollama

<div align="center">
  <img alt="ollama" height="200px" src="https://github.com/ollama/ollama/assets/3325447/0d0b44e2-8f4a-4e99-9b52-a5c1c741c8f7">
</div>

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

## Further Reading on Llama | Meta
- [Llama website](https://ai.meta.com/llama/)
- [Llama technical overview](https://ai.meta.com/resources/models-and-libraries/llama/)
- [Llama GitHub repo](https://github.com/facebookresearch/llama/tree/main)
- [Llama 2 blog](https://ai.meta.com/blog/llama-2/)
- [Llama 2 research article](https://ai.meta.com/research/publications/llama-2-open-foundation-and-fine-tuned-chat-models/)

## 🛡️Responsible AI 
:european_union: **EU's Guidelines on the responsible use of generative AI in research:** https://research-and-innovation.ec.europa.eu/news/all-research-and-innovation-news/guidelines-responsible-use-generative-ai-research-developed-european-research-area-forum-2024-03-20_en

<br>

⚠️ Note: In no circumstance shall the author(s) or copyright holder(s) be held liable for any claim, damages, or other liabilities arising from the utilization of this code, which incorporates several code snippets generated by artificial intelligence (AI), along with open-source contributions from other programmers sourced from platforms including GitHub and other, pursuant to the terms outlined in the MIT License.
