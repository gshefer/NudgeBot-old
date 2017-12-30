FROM fedora

ENV PYCURL_SSL_LIBRARY "openssl"
ENV GIT_SSL_NO_VERIFY false

RUN dnf update -y \
	&& dnf install -y python2-virtualenv gcc postgresql-devel libxml2-devel \
	libxslt-devel zeromq-devel libcurl-devel redhat-rpm-config gcc-c++ openssl-devel \
	libffi-devel python2-devel tesseract freetype-devel \
    && dnf install -y git docutils python vim python-pip gcc \
    && git clone https://github.com/gshefer/NudgeBot.git \
    && cd NudgeBot \
    && pip install -r requirements.txt
