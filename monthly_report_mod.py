# Required Modules

from sshandrrd import *
from serverslist import *
import csv

# Function to Run SSH Command

def sshcmd(cmd):
    ssh.connect(hostname=target_host_check_mk, username= uname_check_mk, password= pwd_check_mk, port= target_port_check_mk)
    stdin, stdout, stderr= ssh.exec_command(cmd)
    ls=stdout.read().decode().split()
    valid_ls=[float(i) for i in ls[2::2] if str(i)!='-nan']
    return valid_ls

def avg(ls):
    avg = sum(ls)/len(ls)
    return avg
    
for k,j in accls.items():
    with open(outpath + f'{k}.csv', 'w', newline='') as csvfile:
        columnames=['Server Name','Server Role','Server Size','Reserved Instance','Total CPU','CPU MAX','CPU AVG',\
            'Total Memory','MEM MAX (%)','MEM AVG(%)','MEM MAX RAW','MEM AVG RAW','Operating System','Application Team','Environment','Observation',\
                'Recommendation','Current Cost', 'Cost Savings']
        thewriter=csv.DictWriter(csvfile,fieldnames=columnames)
        thewriter.writeheader()
        for svr_dict in j:
            if svr_dict['OS'] == 'windows':
                # Generating required commands to run
                svrname = svr_dict['server name chkmk']
                rrdserver = f"cd {svrname}/; "
                rrdcmdcpu = rrdpath["check_mk"] + rrdserver + f"rrdtool fetch {metric_cpu} MAX -r 216000 -s {start} -e {end}"
                rrdcmdmem = rrdpath["check_mk"] + rrdserver + f"rrdtool fetch {metric_mem} MAX -r 216000 -s {start} -e {end}"
                
                # Run SSH Command and store the output in seperate lists

                valid_ls_cpu_max = sshcmd(rrdcmdcpu)
                valid_ls_mem_max = sshcmd(rrdcmdmem)

                # Max and Average Calculation
                try:
                    cpu_max = max(valid_ls_cpu_max)
                    cpu_avg = avg(valid_ls_cpu_max)
                    mem_max = max(valid_ls_mem_max)/1024
                    mem_avg = avg(valid_ls_mem_max)/1024
                    mem_max_per = mem_max / svr_dict['Total Memory'] * 100 
                    mem_avg_per = mem_avg / svr_dict['Total Memory'] * 100 
                except ValueError:
                    cpu_avg, cpu_max, mem_max_per, mem_avg_per = 0,0,0,0
            
            elif svr_dict['OS'] == 'linux':
                svrname = svr_dict['server name chkmk']
                rrdserver = f"cd {svrname}/; "
                rrdcmdcpuuser = rrdpath["check_mk"] + rrdserver + f"rrdtool fetch {metric_cpu_user} MAX -r 216000 -s {start} -e {end}"
                rrdcmdcpusys = rrdpath["check_mk"] + rrdserver + f"rrdtool fetch {metric_cpu_system} MAX -r 216000 -s {start} -e {end}"
                rrdcmdcpuio = rrdpath["check_mk"] + rrdserver + f"rrdtool fetch {metric_cpu_io} MAX -r 216000 -s {start} -e {end}"
                rrdcmdcpusteal = rrdpath["check_mk"] + rrdserver + f"rrdtool fetch {metric_cpu_steal} MAX -r 216000 -s {start} -e {end}"
                rrdcmdcpuguest = rrdpath["check_mk"] + rrdserver + f"rrdtool fetch {metric_cpu_guest} MAX -r 216000 -s {start} -e {end}"
                rrdcmdmemlin =rrdpath["check_mk"] + rrdserver + f"rrdtool fetch {metric_mem_lin} MAX -r 216000 -s {start} -e {end}"
                
                valid_ls_cpu_user = sshcmd(rrdcmdcpuuser)
                valid_ls_cpu_sys = sshcmd(rrdcmdcpusys)
                valid_ls_cpu_io = sshcmd(rrdcmdcpuio)
                valid_ls_cpu_guest = sshcmd(rrdcmdcpuguest)
                valid_ls_cpu_steal = sshcmd(rrdcmdcpusteal)
                valid_ls_mem_max_lin = sshcmd(rrdcmdmemlin)
                
                valid_ls_cpu_linux = [sum(values) for values in zip(valid_ls_cpu_user, valid_ls_cpu_sys, \
                    valid_ls_cpu_guest, valid_ls_cpu_steal, valid_ls_cpu_io)] 
                try:
                    cpu_max = max(valid_ls_cpu_linux)
                    cpu_avg = avg(valid_ls_cpu_linux)
                    mem_max = max(valid_ls_mem_max_lin)/1024000000
                    mem_avg = avg(valid_ls_mem_max_lin)/1024000000
                    mem_max_per = mem_max / svr_dict['Total Memory'] * 100 
                    mem_avg_per = mem_avg / svr_dict['Total Memory'] * 100 
                    
                    if (cpu_avg > 100) or (cpu_max >100):
                        cpu_max, cpu_avg = cpu_max/1.2 , cpu_avg/1.2
                    if (cpu_avg > 100) or (cpu_max >100):
                        cpu_max, cpu_avg = (cpu_max*1.2)/2, (cpu_avg*1.2)/2
                    if (mem_avg_per>100) or (mem_max_per>100):
                        mem_max_per, mem_avg_per = mem_max_per/1.2, mem_avg_per/1.2
                    if (mem_avg_per>100) or (mem_max_per>100):
                        mem_max_per, mem_avg_per = (mem_max_per*1.2)/2, (mem_avg_per*1.2)/2
                except ValueError:
                    cpu_avg, cpu_max, mem_max_per, mem_avg_per = 0,0,0,0
            
            csvdict = {'Server Name' : svr_dict['server name'], 'Server Role' : svr_dict['server role'], \
            'Server Size' : svr_dict['server size'], 'Reserved Instance' : svr_dict['reserved instance'],\
            'Total CPU' : svr_dict['Total CPU'], 'CPU MAX': '%.0f' % cpu_max, 'CPU AVG':  '%.0f' % cpu_avg, \
            'Total Memory': svr_dict['Total Memory'], 'MEM MAX (%)' : '%.0f' % mem_max_per, \
            'MEM AVG(%)' : '%.0f' % mem_avg_per, 'MEM MAX RAW': '%.2f' % mem_max, 'MEM AVG RAW': '%.2f' % mem_avg, 'Operating System': svr_dict['OS'], \
            'Application Team' : svr_dict['Application Team'], 'Environment' : svr_dict['Environment']}
            thewriter.writerow(csvdict)