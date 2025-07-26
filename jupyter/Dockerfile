# ./jupyter/Dockerfile

FROM jupyter/base-notebook:python-3.11.5

# The WORKDIR is /home/jovyan, which is correct.

# Install required Python packages AND the AWS CLI.
RUN pip install --no-cache-dir boto3 psycopg2-binary pandas awscli

# --- THE DEFINITIVE FIX ---
# Copy the entrypoint script AND set its owner to the 'jovyan' user at the same time.
# The user:group for the standard jupyter images is 'jovyan:users'.
COPY --chown=jovyan:users entrypoint.sh /home/jovyan/entrypoint.sh

# Now that 'jovyan' owns the file, this chmod command will succeed.
RUN chmod +x /home/jovyan/entrypoint.sh

# Set the ENTRYPOINT to the script.
ENTRYPOINT ["/home/jovyan/entrypoint.sh"]

# The CMD is the default command passed TO the entrypoint script. This remains correct.
CMD ["start-notebook.sh", \
    "--NotebookApp.allow_origin='*'", \
    "--NotebookApp.allow_remote_access=True", \
    "--NotebookApp.ip='0.0.0.0'", \
    "--NotebookApp.base_url=/jupyter"]