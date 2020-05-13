pip install virtualenv && virtualenv venv

source venv/bin/activate
pip install -r requirements.txt

#!/bin/bash
if ! [ -x "$(command -v redis-server)" ]; then
    echo 'Warning: redis is not installed or is not in the $PATH.' >&2
    curl -O http://download.redis.io/redis-stable.tar.gz
    tar xvzf redis-stable.tar.gz
    rm redis-stable.tar.gz
    cd redis-stable
    make -j8
fi


echo -e "\n\n\n -------------------------------------"
echo 'Now run ./run-redis.sh ./run-celery.sh in seperate terminals'
echo -e 'and start the app \n\n'
echo 'source venv/bin/activate && python app.py'
echo -e "------------------------------------- \n\n\n"
