#!/usr/bin/env python3
"""Simple timing comparison between Unix pipes and Hadoop MapReduce with basic CPU monitoring."""
import subprocess
import time
import logging
import psutil

# Setup basic logging
logging.basicConfig(
    filename='pipeline_timing.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

def monitor_cpu_usage(process_name, start_time):
    """Monitor and log CPU usage of all related processes."""
    try:
        # Get all processes and their CPU usage
        total_cpu = 0
        current_processes = []
        elapsed = time.time() - start_time

        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
            try:
                if proc.info['name'] in ['python3', 'sort']:
                    current_processes.append(proc)
                    total_cpu += proc.info['cpu_percent']
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if total_cpu > 0:
            logging.info(f"{process_name} - Time Elapsed: {elapsed:.1f}s - Total CPU: {total_cpu:.1f}%")

    except Exception as e:
        logging.error(f"Error monitoring CPU: {str(e)}")

def run_unix_pipeline():
    """Run the Unix pipeline and measure time."""
    try:
        # Document count pipeline
        logging.info("Starting document count pipeline")
        start_time = time.time()
        last_update = start_time
        update_interval = 30  # 30 seconds between updates
        
        cmd = "cat ./input/data.csv | ./map0.py | sort | ./reduce0.py"
        process = subprocess.Popen(cmd, shell=True)
        
        while process.poll() is None:
            current_time = time.time()
            if current_time - last_update >= update_interval:
                monitor_cpu_usage("Document Count", start_time)
                last_update = current_time
            time.sleep(1)

        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, cmd)
        
        # Main pipeline
        logging.info("Starting main indexing pipeline")
        start_time = time.time()
        last_update = start_time
        
        cmd = ("cat ./input/data.csv | ./map1.py | sort | ./reduce1.py | "
              "./map2.py | sort | ./reduce2.py | ./map3.py | sort | ./reduce3.py | "
              "./map4.py | sort | ./reduce4.py | ./map5.py | sort | ./reduce5.py")
        process = subprocess.Popen(cmd, shell=True)
        
        while process.poll() is None:
            current_time = time.time()
            if current_time - last_update >= update_interval:
                monitor_cpu_usage("Main Pipeline", start_time)
                last_update = current_time
            time.sleep(1)

        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, cmd)
        
        total_time = time.time() - start_time
        logging.info(f"Unix pipeline completed in {total_time:.2f} seconds")
        return total_time
        
    except subprocess.CalledProcessError as e:
        logging.error(f"Pipeline failed: {str(e)}")
        raise

def run_hadoop_pipeline():
    """Run the Hadoop pipeline and measure time."""
    try:
        logging.info("Starting Hadoop pipeline")
        start_time = time.time()
        last_update = start_time
        update_interval = 30  # 30 seconds between updates
        
        process = subprocess.Popen('./pipeline.sh', shell=True)
        
        while process.poll() is None:
            current_time = time.time()
            if current_time - last_update >= update_interval:
                monitor_cpu_usage("Hadoop Pipeline", start_time)
                last_update = current_time
            time.sleep(1)

        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, './pipeline.sh')
        
        total_time = time.time() - start_time
        logging.info(f"Hadoop pipeline completed in {total_time:.2f} seconds")
        return total_time
        
    except subprocess.CalledProcessError as e:
        logging.error(f"Hadoop pipeline failed: {str(e)}")
        raise

def main():
    try:
        print("Starting performance measurement...")
        print("Check pipeline_timing.log for detailed progress")
        
        # Run Unix pipeline
        unix_time = run_unix_pipeline()
        print(f"\nUnix Pipeline Time: {unix_time:.2f} seconds")
        
        # Brief pause between runs
        time.sleep(5)
        
        # Run Hadoop pipeline
        hadoop_time = run_hadoop_pipeline()
        print(f"Hadoop Pipeline Time: {hadoop_time:.2f} seconds")
        
        # Calculate speedup
        speedup = unix_time / hadoop_time if hadoop_time > 0 else 0
        print(f"\nHadoop Speedup: {speedup:.2f}x")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    main()