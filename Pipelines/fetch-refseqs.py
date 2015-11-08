import re
import os
import gzip

import pandas as pd
from ftplib import FTP

ncbi_ftp = "ftp.ncbi.nlm.nih.gov"
input_report = "Data/genomes_proks_complete_and_chr.csv"
output_folder = "../Data/"
path_folder = re.compile('(?<=ftp.ncbi.nlm.nih.gov).*')
refseq = re.compile('(?<=genomes/all/).*')



try:
    print("Connection to %s" % ncbi_ftp)
    ftp = FTP(ncbi_ftp)
    ftp.login()
    print("Connected")
except:
    print("Connection issues")
    ftp.quit()

df = pd.read_csv(input_report)
nb_rows = len(df)
features = df.dtypes.index
counter = 1
limit = 10 # just for testing

for ftp_address in df["RefSeq FTP"]:
    print("Fetching annotations and genome %i out of %i" % (counter, nb_rows))
    counter += 1
    if(counter == limit): 
        break

    if(ftp_address != "-"):
        folder = re.search(path_folder, ftp_address).group()

        # create destination dir with refseq as folder name
        rs = re.search(refseq, folder).group()
        outdir = os.path.join(output_folder, rs)
        if not os.path.exists(outdir):
            os.makedirs(outdir)
        
        # fetch ftp files for sequence and annotation
        ftp.cwd(folder)
        sequence_handle= "_genomic.fna.gz"
        sequence_file = os.path.join(outdir, rs + sequence_handle)
        features_handle = "_feature_table.txt.gz"
        features_file = os.path.join(outdir, rs + features_handle)
        try:
            ftp.retrbinary('RETR %s' % rs + sequence_handle, open(sequence_file, 'wb').write)
            ftp.retrbinary('RETR %s' % rs + features_handle, open(features_file, 'wb').write)
        except:
            print("Error fetching file %s - does not exit" % rs)
            continue
		
        # extracting fasta 
        with gzip.open(sequence_file, 'rb') as f:
            file_content = f.read()
            output_file = open(os.path.join(outdir, rs + "_genomic.fna"), 'wb')
            output_file.write(file_content)
            output_file.close()
        
        # extracting annotation
        with gzip.open(features_file, 'rb') as f:
            file_content = f.read()
            output_file = open(os.path.join(outdir, rs + "_genomic.gff"), 'wb')
            output_file.write(file_content)	
            output_file.close()
		
        os.remove(features_file)
        os.remove(sequence_file)

        print("%s fetched!" % rs)
        
        # adding meta file
        meta_content = ''
        output_file = open(os.path.join(outdir, rs + "_meta.txt"), 'wb')
        for row_counter in range(nb_rows):
            if(df.ix[row_counter]["RefSeq FTP"] == ftp_address):
                for name in features:
                    meta_content += "#############\n"
                    meta_content += name+":\n"
                    meta_content += str(df.ix[row_counter][name]) + '\n\n'
                    output_file.write(bytes(meta_content, 'UTF-8'))
        output_file.close()
            
print("Closing connection")
ftp.quit()