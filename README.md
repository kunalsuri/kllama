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

To use the Kllama App, you should do the following steps:

<br>

1. Download and install [Ollama](https://ollama.com/) framework in your local machine
   
> The Ollama framework enables easy interaction between your chatbot and the LLM models from the convenience of your local machine

<br>

2. Replicate the Git Repo in your local machine

> We assume that you have cloned the Kllama repo on your local machine. If not, do the following:

```bash
git clone https://github.com/kunalsuri/kllama.git
```

<br>

3. Go to the folder containing Kllama and install the python packages needed to run the Kllama Chatbot

> Kllama.py application needs the following packages: ollama, streamlit. They have been included to the requirements.txt and can be easily installed via the below command:

```bash
pip install -r requirements.txt
```

<br>

⚠️ Recommendation: we recommend that the users create a new python virtual environment and install the python packages via requirement.txt (in Step 3 above) to keep their python installation clean.

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

⚠️ Note: I'm not affiliated with [Replicate.com](https://replicate.com) company; I simply found their service interesting and decided to use it.

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



