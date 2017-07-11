#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import requests
try:
   import cPickle as pickle
except:
   import pickle
from lxml import html
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, Job

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

data = pickle.load(open("data.dat","rb"))
address = data[0]
hashtarget = data[1]
lesser_loops = data[2]


def start(bot, update):
    update.message.reply_text('This bot was built for one purpose: tracking ZCash mining speed at zcash.flypool.org')
    update.message.reply_text('To start tracking type /address <mining address>')
    update.message.reply_text('Please type /help for more information on commands')

def run_help(bot, update):
    update.message.reply_text('All Commands: /start /help /addresss <mining address> /track <target hash rate> /stop')

def run_address(bot, update, args):
    try:
        address[update.message.chat_id] = args[0]
        update.message.reply_text('Address - %s' % (address[update.message.chat_id]))
        update.message.reply_text('Reset with /address <mining address>')
        update.message.reply_text('Start Tracking with /track <target kH/s rate>')
        pickle.dump([address,hashtarget,lesser_loops],open("data.dat","wb"))
        #print address[update.message.chat_id]
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /address <mining address>')

def track(bot, update, args, job_queue, chat_data):
    try:
        hashtarget[update.message.chat_id] = args[0]
        lesser_loops[update.message.chat_id] = 0
        update.message.reply_text('Target Hash Rate - %s kH/s' % (hashtarget[update.message.chat_id]))
        pickle.dump([address,hashtarget,lesser_loops],open("data.dat","wb"))
        #print print hashtarget[update.message.chat_id]
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /track <hash rate>')

    job_message = Job(checkhash,3600,repeat = True, context = update.message.chat_id)
    chat_data['job'] = job_message
    job_queue.put(job_message, next_t=0.0)

def run_stop(bot, update, job_queue, chat_data):
    if('job' not in chat_data):
        update.message.reply_text('No Active Tracking')
    else:
        job_message = chat_data['job']
        job_message.schedule_removal()
        bot.sendMessage(chat_id = update.message.chat_id, text ='*Hash Tracking Stopped*', parse_mode = "Markdown")
        del chat_data['job']


  

    
def checkhash(bot, job):
    print "Checking Hash"
    page = requests.get('http://zcash.flypool.org/miners/%s' %(address[job.context]))
    tree = html.fromstring(page.content)
    currenthash = tree.xpath("/html/body/div[@class='container-fluid']/div[@class='row']/div[@class='col-lg-8 col-8-10']/div[@id='home']/div[@class='row'][3]/div[@class='col-md-4 text-center'][1]/div[@class='panel panel-warning']/div[@class='panel-body']/h4/span[@class='just_span'][1]/text()")
    currenthash = float((str(currenthash).split(" ")[0])[2:])
    print currenthash
    print 'Before For - %s' %(lesser_loops[job.context])
    if(currenthash < hashtarget[job.context]):
        lesser_loops[job.context] += 1
        print 'Inside For'
        print lesser_loops[job.context]
        if(lesser_loops[job.context] == 1):
            bot.sendMessage(chat_id = job.context, text = "*Current Hash Rate = %s kH/s*" %(currenthash), parse_mode = "Markdown")
            bot.sendMessage(chat_id = job.context, text = "*Hash Rate Below Target of %s kH/s*" %(hashtarget[job.context]), parse_mode = "Markdown")
            bot.sendMessage(chat_id = job.context, text = "😡 😡 😡 😡 😡 😡 😡 😡 😡 😡")
        if(lesser_loops[job.context] > 1 and (lesser_loops[job.context]%6) == 0):
            bot.sendMessage(chat_id = job.context, text = "*Current Hash Rate = %s kH/s*" %(currenthash), parse_mode = "Markdown")
            bot.sendMessage(chat_id = job.context, text = "*Hash Rate Below Target of %s kH/s*" %(hashtarget[job.context]), parse_mode = "Markdown")
            bot.sendMessage(chat_id = job.context, text = "😡 😡 😡 😡 😡 😡 😡 😡 😡 😡")
        
    if(currenthash >= hashtarget[job.context]):
        lesser_loops[job.context] = 0


def error(bot, update, error):
    logging.warning('Update "%s" caused error "%s"' % (update, error))


# Create the Updater and pass it your bot's token.
updater = Updater("apikey")
job_queue = updater.job_queue


updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(CommandHandler('help', run_help))
updater.dispatcher.add_handler(CommandHandler('track', track, pass_args = True, pass_job_queue=True,pass_chat_data=True))
updater.dispatcher.add_handler(CommandHandler('stop', run_stop, pass_job_queue=True,pass_chat_data=True))
updater.dispatcher.add_handler(CommandHandler('address', run_address, pass_args= True))
updater.dispatcher.add_error_handler(error)

# Start the Bot
updater.start_polling()

# Run the bot until the user presses Ctrl-C or the process receives SIGINT,
# SIGTERM or SIGABRT
updater.idle()

