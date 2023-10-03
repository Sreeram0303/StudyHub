from django.shortcuts import render,redirect
from django.contrib import messages
from django.http import HttpResponse
from .models import *
from .forms import *
from django.db.models import Q
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required #For restricting users there are couple of other ways too
# Create your views here.


# rooms =[
#     {"id":1,"name":"Lets learn python"},
#     {"id":2,"name":"Frontend developers"},
#     {"id":3,"name":"Design"}
# ]


def loginpage(request):
    page = 'login'
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        email = request.POST['email'].lower()
        password = request.POST['password']
        try:
            user =User.objects.get(username = email)
        except:
            messages.error(request,"User does not exist")
        user = authenticate(request,email=email,password=password)

        if user is not None:
            login(request,user)
            return redirect('home')
        else:
            messages.error(request,"User name or Password doesn't exist")
    context = {'page':page}
    return render(request,'base/login_register.html',context)


def registerpage(request):
    form = MyUserCreationForm()
    
    if request.user.is_authenticated:
        return redirect("home")
    
    if request.method == "POST":
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            print(request.POST)
            user = form.save(commit=False) #To manipulate the data before saving into the database
            user.username = user.username.lower()
            user.save()
            login(request,user)
            return redirect('home')
        else:
            messages.error(request,"An error ocurred during registration")
    context = {'form':form}
    return render(request,'base/login_register.html',context)



def logoutpage(request):
    logout(request)
    return redirect('home')


def home(request):
    q= request.GET.get('q') if request.GET.get("q") != None else ''
    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
        ) 
    # To enable the search even half of the word is typed
    topic = Topic.objects.all()[:5]
    rooms_count = rooms.count()
    room_messages = Messages.objects.filter(Q(room__topic__name__icontains = q))
    context = {"rooms":rooms,"topics":topic,'rooms_count':rooms_count,'room_messages':room_messages}
    return render(request,"base/home.html",context)

def room(request,pk):
    room = Room.objects.get(id = pk)
    room_messages = room.messages_set.all()
    participants = room.participants.all()
    if request.method == "POST":
        message = Messages.objects.create(
            user = request.user,
            room = room,
            body = request.POST['body']
        )
        room.participants.add(request.user)#to add him as participant automatically
        return redirect('room', pk = room.id)

    context = {'room':room,'room_messages':room_messages,'participants':participants}
    return render(request,"base/room.html",context)

def userProfile(request,pk):
    user  = User.objects.get(id = pk)
    rooms = user.room_set.all()
    room_messages = user.messages_set.all()
    topics = Topic.objects.all()
    context = {'user':user,'rooms':rooms,'room_messages':room_messages,'topics':topics}
    return render(request,"base/profile.html",context)


@login_required(login_url='login')
def create_room(request):
    form = RoomForm()
    topics = Topic.objects.all()
    if request.method == "POST":
        topic_name = request.POST['topic']
        topic,created = Topic.objects.get_or_create(name = topic_name)

        Room.objects.create(
            host = request.user,
            topic = topic,
            name = request.POST['name'],
            description = request.POST['description']
        )
        return redirect('home')
    context = {'form':form,'topics':topics}
    return render(request,'base/room_form.html',context)

@login_required(login_url='login')
def update_room(request,pk):
    room = Room.objects.get(id = pk)
    form = RoomForm(instance=room)
    topics = Topic.objects.all()
    # Even after after restrictig the user using decorators if one knows the id of the other room
    # they can mess with the data so to restrict that we check whether the user trying to update
    # and the owner of the room are same or not using the below if condition
    if request.user != room.host:
        return HttpResponse("You are not allowed here") 

    if request.method == "POST":
        topic_name = request.POST['topic']
        topic,created = Topic.objects.get_or_create(name = topic_name)
        room.name = request.POST['name']
        room.topic = topic
        room.description = request.POST['description']
        room.save()
        return redirect("home")
    context = {"form":form,'topics':topics,'room':room}
    return render(request,'base/room_form.html',context)

@login_required(login_url='login')
def delete_room(request,pk):
    room = Room.objects.get(id = pk)
    context = {'obj':room}

    if request.user != room.host:
        return HttpResponse("You are not allowed here") 
    
    if request.method == "POST":
        room.delete()
        return redirect('home')
    return render(request,'base/delete.html',context)

@login_required(login_url='login')
def delete_message(request,pk):
    message = Messages.objects.get(id = pk)
    context = {'obj':message}
    room = message.room
    print(room)
    if request.user != message.user:
        return HttpResponse("You are not allowed here") 
    
    if request.method == "POST":
        message.delete()
        return redirect('room',pk = room.id)
    return render(request,'base/delete.html',context)


@login_required(login_url="login")
def updateUser(request):
    user = request.user
    form = UserForm(instance = user)

    if request.method == 'POST':
        form = UserForm(request.POST,request.FILES,instance = user)
        if form.is_valid():
            form.save()
            return redirect('user-profile' ,pk=user.id)
    context = {'form':form}
    return render(request,'base/update-user.html',context)

def topicsPage(request):
    q= request.GET.get('q') if request.GET.get("q") != None else ''
    topics = Topic.objects.filter(name__icontains = q)

    return render(request,'base/topics.html',{'topics':topics})

def activityPage(request):
    room_messages = Messages.objects.all()
    return render(request,'base/activity.html',{'room_messages':room_messages})