FROM n8nio/n8n:latest
USER root
COPY marketmind_ia_workflow.json /home/node/workflow.json
RUN chown node:node /home/node/workflow.json
COPY start.sh /home/node/start.sh
RUN chmod +x /home/node/start.sh
USER node
ENTRYPOINT ["/bin/sh", "/home/node/start.sh"]
