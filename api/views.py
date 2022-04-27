from ensurepip import version

from rest_framework.authentication import  TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from rest_framework.response import Response

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token



from rest_framework.decorators import api_view, authentication_classes, permission_classes

from .models import Restaurant, Menu, Vote

from django.forms.models import model_to_dict
from .serializers import MenuSerializer

from django.db.models import Case, When

import pyrankvote
from pyrankvote import Candidate, Ballot




import json
from datetime import date


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def addRestaurant(request):
    print(request.version)
    data =  request.data
    restaurant = Restaurant()
    restaurant.name = data['name']

    restaurant.save()

    return Response( model_to_dict(restaurant, ['id', 'name']))
    

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def addMenuToRestaurant(request):
    try:
        restaurant = Restaurant.objects.get(pk=request.data['restaurant_id']) 
    except:
        return Response({'errors': ['Restaurant does not exist']}, 404)

    # if Menu.objects.filter(restaurant=restaurant, created_at=date.today()).count() > 0:
    #     return Response({'errors': ['Restaurant does already have a menu for today']}, 401)

    #Make sure that this restaurant does not already have a menu for today
    menu = Menu(restaurant = restaurant, description = request.data['description'] , created_at=date.today())
    menu.save()

    return Response( model_to_dict(menu, ['id', 'created_at']))


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def getCurrentDayMenus(request):
    menus = Menu.objects.filter(created_at=date.today())
    return Response(MenuSerializer(menus,many=True).data)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def voteForRestaurantMenu(request):
    # print(request.user)
    #TODO: Check the request.version and comply with it
    

    if request.version == '1.0':
        try:
            menu = Menu.objects.get(pk=request.data['menu_id'])
            voted = Vote.objects.filter(created_at=date.today(), user=request.user).exists()
            if voted : 
                return Response({'errors': ['You have already voted today']}, 401)

            vote = Vote(menu=menu, user=request.user, created_at=date.today(), rank=1)
            vote.save()

            #todo : Add the voting
        except:
            return Response({'errors': ['Menu Does not exist']}, 404)

    elif request.version == '1.1':
        menuIds = request.data['menu_ids']
        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(menuIds)])
        menus = Menu.objects.filter(pk__in=menuIds).order_by(preserved)

        voted = Vote.objects.filter(created_at=date.today(), user=request.user).exists()
        if voted : 
            return Response({'errors': ['You have already voted today']}, 401)

        counter = 1
        for menu in menus:
            vote = Vote(menu=menu, user=request.user, created_at=date.today(), rank=counter)
            vote.save()
            counter += 1
            pass

        return Response(menuIds)
    
    return Response()


"""
We use the ranked choice idea to rank menu, similar to presidential voting
"""

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def getCurrentDayVotingResults(request):
    #Create menu candidates from the available menus today
    menus = Menu.objects.filter(created_at=date.today())
    candidates = [Candidate(str(menu.id)) for menu in menus]

    #From today's votes, map users to their ordered menu choices
    userVotes = {}
    votes = Vote.objects.filter(created_at=date.today())
    for vote in votes:
        if vote.user_id not in userVotes:
            userVotes[vote.user_id] = []
        userVotes[vote.user_id].append(vote.menu_id)


    #Build the ballots array with all the choices for each vote
    ballots = []
    for userVote in userVotes:
        menuIds = userVotes[userVote]
        #Find a candidate (Menu) object
        rankedCandidates = []
        for menuId in menuIds:
            candidate = next((x for x in candidates if x.name == str(menuId)), None)
            rankedCandidates.append(candidate)

        ballots.append(Ballot(ranked_candidates=rankedCandidates))
    


    # Compute the voting rsults and extract the winner menu
    election_result = pyrankvote.instant_runoff_voting(candidates, ballots)

    winners = election_result.get_winners()
    if len(winners) > 0:
        winnerMenu = Menu.objects.get(pk=int(winners[0].name))
        return Response({'menu' : MenuSerializer(winnerMenu).data})
    return Response({'errors' : ['No voting today']})


@api_view(['POST'])
def login(request):
    try:
        username = request.data['username']
        password = request.data['password']
        userExists = User.objects.filter(username=username).exists()
        if userExists:
            user = authenticate(request, username=username, password=password)
            if not user:
                return Response({'errors' : ['Error in credentials, make sure user exists and password is correct']})
            
            token = Token.objects.create(user=user)
            return Response({'token' : model_to_dict(token, ['key', 'created'])})

        else:
            return Response({'errors' : ['Error in credentials, make sure user exists and password is correct']})

        pass 
    except:
        return Response({'errors' : ['Error in params, you need username, and password to login']})


@api_view(['POST'])
def register(request):
    try:
        firstname = request.data['firstname']
        lastname = request.data['lastname']
        email = request.data['email']
        username = request.data['username']
        password = request.data['password']
        userExists = User.objects.filter(username=username).exists()
        if userExists:
            return Response({'errors' : ['User does already exists']})

        user = User.objects.create_user(username, email, password)
        user.first_name = firstname
        user.last_name = lastname
        user.save()
        return Response(model_to_dict(user, ['username', 'email']))

    except:
        return Response({'errors' : ['Missin params, firstname, lastname, email, username, password are all required']})



