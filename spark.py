# Datasets:
# 	July -> ftp://ita.ee.lbl.gov/traces/NASA_access_log_Jul95.gz
# 	August -> ftp://ita.ee.lbl.gov/traces/NASA_access_log_Aug95.gz


from pyspark import SparkConf, SparkContext
from operator import add


conf = (SparkConf()
         .setMaster("local")
         .setAppName("SPark")
         .set("spark.executor.memory", "2g"))
sc = SparkContext(conf = conf)


july = sc.textFile('access_log_Jul95')
july = july.cache()

august = sc.textFile('access_log_Aug95')
august = august.cache()


# number of distinct hosts
july_count = july.flatMap(lambda line: line.split(' ')[0]).distinct().count()
august_count = august.flatMap(lambda line: line.split(' ')[0]).distinct().count()
print('Distinct hosts on July: %s' % july_count)
print('Distinct hosts on August %s' % august_count)


# number of 404 errors
def response_code_404(line):
    try:
        code = line.split(' ')[-2]
        if code == '404':
            return True
    except:
        pass
    return False
    
july_404 = july.filter(response_code_404).cache()
august_404 = august.filter(lambda line: line.split(' ')[-2] == '404').cache()

print('404 errors in July: %s' % july_404.count())
print('404 errors in August %s' % august_404.count())


# 5 most frequent endpoints causing 404 errors
def top5_endpoints(rdd):
    endpoints = rdd.map(lambda line: line.split('"')[1].split(' ')[1])
    counts = endpoints.map(lambda endpoint: (endpoint, 1)).reduceByKey(add)
    top = counts.sortBy(lambda pair: -pair[1]).take(5)
    
    print('\nTop 5 most frequent 404 endpoints:')
    for endpoint, count in top:
        print(endpoint, count)
        
    return top

top5_endpoints(july_404)
top5_endpoints(august_404)


# 404 errors per day
def daily_count(rdd):
    days = rdd.map(lambda line: line.split('[')[1].split(':')[0])
    counts = days.map(lambda day: (day, 1)).reduceByKey(add).collect()
    
    print('\n404 errors per day:')
    for day, count in counts:
        print(day, count)
        
    return counts

daily_count(july_404)
daily_count(august_404)


# Total byte count
def accumulated_byte_count(rdd):
    def byte_count(line):
        try:
            count = int(line.split(" ")[-1])
            if count < 0:
                raise ValueError()
            return count
        except:
            return 0
        
    count = rdd.map(byte_count).reduce(add)
    return count

print('Total byte count in July: %s' % accumulated_byte_count(july))
print('Total byte count in August: %s' % accumulated_byte_count(august))


sc.stop()