from win32com import client as wc
import os
import glob
import multiprocessing
from multiprocessing import freeze_support

word = wc.Dispatch('Word.Application')
word.Visible = 0

def word2pdf(input, output):    
    #for i, path in enumerate(paths):
    #print ("Transferring [{}]".format(i), path)
    doc = word.Documents.Open(input)
    doc.SaveAs(output, 17)
    doc.Close()

docs = glob.glob("lyrics/*.docx")
docs = [doc for doc in docs if not "~$" in doc]
for i, path in enumerate(docs):
    input = os.path.join('F:\\feitsui\\', path)
    output = os.path.join('F:\\feitsui\\', 'pdf', os.path.splitext(os.path.basename(path))[0] + ".pdf" )
    if not os.path.exists(output):
        print ("Converting [{}]".format(i), path)
        word2pdf(input, output)

word.Quit()

"""
num_workers = 12
blk_size = len(docs) // 11
workers = []
#for i in range(12):
i=0
word2pdf(docs[i*blk_size: (i+1)*blk_size])
"""
"""
if __name__ == "__main__":    
    #freeze_support()
    docs = glob.glob("lyrics/*.docx")
    #for i, path in enumerate(docs):
    #    word2pdf(path)
    num_workers = 12
    blk_size = len(docs) // 11
    workers = []
    for i in range(12):
        print (i*blk_size, (i+1)*blk_size)
        worker = multiprocessing.Process(target=word2pdf, args = (docs[i*blk_size: (i+1)*blk_size], ))        
        workers.append(worker)
    
    for worker in workers:
        worker.start()

    for worker in workers:
        worker.join()
"""
"""
    pool = multiprocessing.Pool(12)
    for i, path in enumerate(docs):
        pool.apply_async(word2pdf, args=(path, apps[i%12]))

    pool.close()
    pool.join()
"""
        