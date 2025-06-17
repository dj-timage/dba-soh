import ftplib
import pandas as pd
import os
import tempfile
import logging
from datetime import datetime
import time
import random

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FTP server credentials and file paths
ftp_server = 'integrations.prospeedracing.com.au'
ftp_user = 'u471835855.DBASOH'
ftp_pass = 'dbaSOH123!'
file1 = '/DBAsoh.csv'
file2 = '/DBAVICsoh.csv'
#file3 = '/DBABRISsoh.csv'
#file4 = '/DBATVLsoh.csv'
#file5 = '/DBAADLsoh.csv'
output_file = 'consolidated_inventory.csv'  # The file to save back to FTP

# Save to the system's temporary directory to avoid permission issues
temp_dir = tempfile.gettempdir()
local_output_file = os.path.join(temp_dir, output_file)

# Function to download files from FTP
def download_file(ftp, filename, local_filename):
    with open(local_filename, 'wb') as f:
        ftp.retrbinary(f'RETR ' + filename, f.write)

def upload_file_with_retry(ftp, local_filename, remote_filename, max_retries=3):
    """Upload file with retry logic and random delay to handle concurrent access"""
    for attempt in range(max_retries):
        try:
            # Add random delay to help avoid concurrent access
            time.sleep(random.uniform(1, 3))
            with open(local_filename, 'rb') as f:
                ftp.storbinary(f'STOR ' + remote_filename, f)
            return True
        except ftplib.error_perm as e:
            if attempt < max_retries - 1:
                logger.warning(f"Upload attempt {attempt + 1} failed: {str(e)}. Retrying...")
                time.sleep(random.uniform(2, 5))  # Wait before retry
            else:
                raise

try:
    # Log start of process
    logger.info(f"Starting inventory update at {datetime.now()}")
    
    # Connect to FTP server
    ftp = ftplib.FTP(ftp_server)
    ftp.login(ftp_user, ftp_pass)
    logger.info("Connected to FTP server")

    # Download both CSV files from FTP
    download_file(ftp, file1, 'file1_local.csv')
    download_file(ftp, file2, 'file2_local.csv')
    #download_file(ftp, file3, 'file3_local.csv')
    #download_file(ftp, file4, 'file4_local.csv')
    #download_file(ftp, file5, 'file5_local.csv')
    logger.info("Downloaded CSV files")

    # Load the CSV files into pandas DataFrames with tab delimiter
    df1 = pd.read_csv('file1_local.csv', 
                      encoding='utf-16',
                      delimiter='\t',  # Changed to tab delimiter
                      on_bad_lines='skip')
    df2 = pd.read_csv('file2_local.csv', 
                      encoding='utf-16',
                      delimiter='\t',  # Changed to tab delimiter
                      on_bad_lines='skip')
    #df3 = pd.read_csv('file3_local.csv', 
    #              encoding='utf-16',
    #              delimiter='\t',
    #              on_bad_lines='skip')
    #df4 = pd.read_csv('file4_local.csv', 
    #                encoding='utf-16',
    #                delimiter='\t',
    #                on_bad_lines='skip')
    #df5 = pd.read_csv('file5_local.csv', 
    #                encoding='utf-16',
    #                delimiter='\t',
    #                on_bad_lines='skip')    

    
    # Print column headers of all files
    print(f"File 1 columns: {df1.columns.tolist()}")
    print(f"File 2 columns: {df2.columns.tolist()}")
    #print(f"File 3 columns: {df3.columns.tolist()}")
    #print(f"File 4 columns: {df4.columns.tolist()}")
    #print(f"File 5 columns: {df5.columns.tolist()}")

    # Print first few rows of each file
    print("\nFirst few rows of file 1:")
    print(df1.head())
    print("\nFirst few rows of file 2:")
    print(df2.head())
    #print("\nFirst few rows of file 3:")
    #print(df3.head())
    #print("\nFirst few rows of file 4:")
    #print(df4.head())
    #print("\nFirst few rows of file 5:")
    #print(df5.head())

    
    # Combine the DataFrames
    #combined_df = pd.concat([df1, df2, df3, df4, df5])
    combined_df = pd.concat([df1, df2])

    # Group by 'Item Code' and sum the 'Available' values
    consolidated_df = combined_df.groupby('Item Code', as_index=False).agg({'Available': 'sum'})

    # Rename the columns as required
    consolidated_df.rename(columns={
        'Item Code': 'SKU',
        'Available': 'Inventory'
    }, inplace=True)

    # Ensure the 'Inventory' column is an integer
    consolidated_df['Inventory'] = consolidated_df['Inventory'].astype(int)

    # Save the consolidated DataFrame to a local CSV file
    consolidated_df.to_csv(local_output_file, index=False)

    # Upload the final CSV back to the FTP server with retry logic
    upload_file_with_retry(ftp, local_output_file, output_file)
    logger.info("Uploaded consolidated inventory file")

    # Close the FTP connection
    ftp.quit()
    logger.info(f"Process completed successfully at {datetime.now()}")

except Exception as e:
    logger.error(f"Error during process: {str(e)}")
    if 'ftp' in locals():
        try:
            ftp.quit()
        except:
            pass
    raise

print(f"Consolidation completed and saved as '{output_file}' on the FTP server.")
