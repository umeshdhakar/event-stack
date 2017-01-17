import datetime

import cloudinary
import cloudinary.uploader
import cloudinary.api
import tablib
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.exceptions import FieldDoesNotExist
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

# Create your views here.
from website.event_form import EventForm
from website.forms import UserForm, UserProfileForm, BasicProfileForm, CurrentAProfileForm,PreviousAProfileForm,AdditionalProfileForm
from website.models import Event, UserProfile, Entries, EventFields,Invite
cloudinary.config(
  cloud_name="tej-mycloud",
  api_key="191512437269526",
  api_secret="s8ETWsWk-Z0N4z_MnPJ4xnWkqPc"
)


def index(request):
    return render(request, 'website/index.html')


def profile(request):
    if request.user.is_authenticated():
        return render(request, 'website/profile.html')
    else:
        return redirect('/')


def register(request):

    if not request.user.is_authenticated():

            # A boolean value for telling the template whether the registration was successful.
            # Set to False initially. Code changes value to True when registration succeeds.
            registered = False

            # If it's a HTTP POST, we're interested in processing form data.
            if request.method == 'POST':
                # Attempt to grab information from the raw form information.
                # Note that we make use of both UserForm and UserProfileForm.
                user_form = UserForm(data=request.POST)
                profile_form = UserProfileForm(data=request.POST)

                # If the two forms are valid...
                if user_form.is_valid() and profile_form.is_valid():
                    # Save the user's form data to the database.
                    user = user_form.save()

                    # Now we hash the password with the set_password method.
                    # Once hashed, we can update the user object.
                    user.set_password(user.password)
                    user.save()

                    # Now sort out the UserProfile instance.
                    # Since we need to set the user attribute ourselves, we set commit=False.
                    # This delays saving the model until we're ready to avoid integrity problems.
                    profile = profile_form.save(commit=False)
                    profile.user = user
                    # Now we save the UserProfile model instance.
                    profile.save()

                    # Update our variable to tell the template registration was successful.
                    registered = True

                # Invalid form or forms - mistakes or something else?
                # Print problems to the terminal.
                # They'll also be shown to the user.
                else:
                    print("User Form Errors :" + str(user_form.errors) + "Profile Form Errors" + str(profile_form.errors))

            # Not a HTTP POST, so we render our form using two ModelForm instances.
            # These forms will be blank, ready for user input.
            else:
                user_form = UserForm()
                profile_form = UserProfileForm()

            # Render the template depending on the context.
            return render(request, 'website/index.html', {'user_reg_form': user_form, 'user_profile_form': profile_form,
                                                          'registered': registered})
    else:
            return redirect('/dashboard/')


def user_login(request):

    # If the request is a HTTP POST, try to pull out the relevant information.
    if request.method == 'POST':
        # Gather the username and password provided by the user.
        # This information is obtained from the login form.
                # We use request.POST.get('<variable>') as opposed to request.POST['<variable>'],
                # because the request.POST.get('<variable>') returns None, if the value does not exist,
                # while the request.POST['<variable>'] will raise key error exception
        username = request.POST.get('username_login')
        password = request.POST.get('pass_login')

        # Use Django's machinery to attempt to see if the username/password
        # combination is valid - a User object is returned if it is.
        user = authenticate(username=username, password=password)

        # If we have a User object, the details are correct.
        # If None (Python's way of representing the absence of a value), no user
        # with matching credentials was found.
        if user:
            # Is the account active? It could have been disabled.
            if user.is_active:
                # If the account is valid and active, we can log the user in.
                # We'll send the user back to the homepage.
                login(request, user)
                return redirect('/dashboard/')
            else:
                # An inactive account was used - no logging in!
                return render(request, 'website/index.html', {'login_error': 'Your account is disabled!'})
        else:
            # Bad login details were provided. So we can't log the user in.
            # print "Invalid login details: {0}, {1}".format(username, password)
            return render(request, 'website/index.html', {'login_error': 'Invalid Credentials'})

    # The request is not a HTTP POST, so display the login form.
    # This scenario would most likely be a HTTP GET.
    else:
        # No context variables to pass to the template system, hence the
        # blank dictionary object...
        return render(request, 'website/index.html')


def user_logout(request):
    if request.user.is_authenticated():
        logout(request)
        global message
        message = ''
    else:
        return redirect('/dashboard/')
    return redirect('/')


def user_profile(request):

    if request.user.is_authenticated():
        user = get_object_or_404(User, username=request.user.username)
        userprofile = get_object_or_404(UserProfile, user=user)

        user_form = UserForm(instance=user)
        basic_profile_form = BasicProfileForm(instance=userprofile)
        current_profile_form = CurrentAProfileForm(instance=userprofile)
        previous_profile_form = PreviousAProfileForm(instance=userprofile)
        additional_profile_form = AdditionalProfileForm(instance=userprofile)
        message = ""
        upload_error = ""

        if request.POST.get('update') == 'update_basic':
            if request.method == 'POST':
                basic_profile_form = BasicProfileForm(request.POST, request.FILES, instance=userprofile)

                if basic_profile_form.is_valid():

                    if 'passphoto' in request.FILES:
                        if request.FILES['passphoto']:
                            if request.FILES['passphoto'].size <= 300000:
                                p_up_count = userprofile.p_up_count
                                p_up_count += 1
                                if userprofile.passphoto is not None and userprofile.passphoto!="":
                                    cloudinary.uploader.destroy(userprofile.passphoto, invalidate=True, type='authenticated')
                                cloudinary.uploader.upload(request.FILES['passphoto'],
                                                           public_id=user.username + "/passportV" + str(p_up_count),
                                                           type='authenticated')
                                userprofile.passphoto = user.username + "/passportV" + str(p_up_count)
                                userprofile.p_up_count = p_up_count
                            else:
                                upload_error = "File size too large!"
                    if 'sign' in request.FILES:
                        if request.FILES['sign']:
                            if request.FILES['sign'].size <= 300000:
                                s_up_count = userprofile.s_up_count
                                s_up_count += 1
                                if userprofile.sign is not None and userprofile.sign != "":
                                    cloudinary.uploader.destroy(userprofile.sign, invalidate=True, type='authenticated')
                                cloudinary.uploader.upload(request.FILES['sign'],
                                                           public_id=user.username + "/signV" + str(s_up_count),
                                                           type='authenticated')
                                userprofile.sign = user.username + "/signV" + str(s_up_count)
                                userprofile.s_up_count = s_up_count
                            else:
                                upload_error = "File size too large!"
                    userprofile = basic_profile_form.save()
                    userprofile.age = int((datetime.date.today() - userprofile.dob).days / 365.25)
                    userprofile.save()
                    message = 'Successfully Updated!'
                else:
                    print("Profile Form Errors" + str(basic_profile_form.errors))
        else:
            if request.POST.get('update') == 'update_current':
                if request.method == 'POST':
                    current_profile_form = CurrentAProfileForm(data=request.POST, instance=userprofile)

                    if current_profile_form.is_valid():
                        userprofile = current_profile_form.save()
                        userprofile.save()
                        message = 'Successfully Updated!'
                    else:
                        print("Profile Form Errors" + str(current_profile_form.errors))
            else:
                if request.POST.get('update') == 'update_previous':
                    if request.method == 'POST':
                        previous_profile_form = PreviousAProfileForm(data=request.POST, instance=userprofile)

                        if previous_profile_form.is_valid():
                            userprofile = previous_profile_form.save()
                            userprofile.save()
                            message = 'Successfully Updated!'
                        else:
                            print("Profile Form Errors" + str(previous_profile_form.errors))
                else:
                    if request.POST.get('update') == 'update_additional':
                        if request.method == 'POST':
                            additional_profile_form = AdditionalProfileForm(data=request.POST, instance=userprofile)

                            if additional_profile_form.is_valid():
                                userprofile = additional_profile_form.save()
                                userprofile.save()
                                message = 'Successfully Updated!'
                            else:
                                print("Profile Form Errors" + str(additional_profile_form.errors))
                    else:
                        message = ""
        currpassphoto = cloudinary.CloudinaryImage(userprofile.passphoto).image(sign_url=True, width=0.5,
                                                                                type='authenticated')

        sign = cloudinary.CloudinaryImage(userprofile.sign).image(sign_url=True, width=0.3, type='authenticated')
        return render(request, 'website/profile.html', {'message:': message,
                                                        'user_form': user_form,
                                                        'basic_profile_form': basic_profile_form,
                                                        'current_profile_form': current_profile_form,
                                                        'previous_profile_form': previous_profile_form,
                                                        'additional_profile_form': additional_profile_form,
                                                        'currpassphoto': currpassphoto,
                                                        'sign': sign,
                                                        'upload_error': upload_error})
    else:
        return redirect('/')


message = ''
message_error = ''


def new_event(request):
    if request.user.is_authenticated():
        if request.method == 'POST':
            event_form = EventForm(request.POST)
            if event_form.is_valid():
                event = event_form.save(commit=False)
                event.by = request.user.id
                event.save()
                global message
                global message_error

                for cat in request.POST.getlist('category'):
                    invite = Invite(eve=event, category=cat)
                    invite.save()

                selected_fields = request.POST.getlist('fields')
                fields = EventFields()

                if 'name' in selected_fields:
                    fields.name = True
                if 'age' in selected_fields:
                    fields.age = True
                if 'gender' in selected_fields:
                    fields.gender = True
                if 'dob' in selected_fields:
                    fields.dob = True
                if 'contact' in selected_fields:
                    fields.contact = True
                if 'alternate_contact' in selected_fields:
                    fields.alternate_contact = True
                if 'passphoto' in selected_fields:
                        fields.passphoto = True
                if 'sign' in selected_fields:
                    fields.sign = True

                if 'class_rno' in selected_fields:
                    fields.class_rno = True
                if 'univ_rno' in selected_fields:
                    fields.univ_rno = True
                if 'semester' in selected_fields:
                    fields.semester = True
                if 'section' in selected_fields:
                    fields.section = True
                if 'batch' in selected_fields:
                    fields.batch = True
                if 'year' in selected_fields:
                    fields.year = True
                if 'branch' in selected_fields:
                    fields.branch = True
                if 'college' in selected_fields:
                    fields.college = True

                # previous academic details skipped

                if 'father_name' in selected_fields:
                    fields.father_name = True
                if 'father_contact' in selected_fields:
                    fields.father_contact = True
                if 'father_occupation' in selected_fields:
                    fields.father_occupation = True
                if 'mother_name' in selected_fields:
                    fields.mother_name = True
                if 'mother_contact' in selected_fields:
                    fields.mother_contact = True
                if 'mother_occupation' in selected_fields:
                    fields.mother_occupation = True
                if 'guardian_contact' in selected_fields:
                    fields.guardian_contact = True
                if 'present_address' in selected_fields:
                    fields.present_address = True
                if 'permanent_address' in selected_fields:
                    fields.permanent_address = True

                fields.event = event
                fields.save()
                message = 'Event ' + event.name + ' created Successfully.'
            else:
                message_error = 'Details are incorrect.'
            return redirect(dashboard)

        else:
            redirect(dashboard)


def delete_event(request, eventid):
    myevent = Event.objects.get(id=eventid)
    event_name = myevent.name
    if myevent.by == request.user.id:
        myevent.delete()
        global message
        message = event_name+' deleted successfully.'
        return redirect(dashboard)
    else:
        return redirect(dashboard)


def dashboard(request):
    if request.user.is_authenticated():
        event_form = EventForm()
        my_events = Event.objects.filter(by=request.user.id)
        global message
        global message_error
        user_category = UserProfile.objects.get(user=request.user).branch
        current_user_id = request.user.id
        expired_events = Invite.objects.filter(category=user_category).filter(eve__end_date__lt=datetime.date.today())\
            .exclude(eve__by=current_user_id)
        registered = Entries.objects.filter(userprofile__user_id=current_user_id)
        active_events = Invite.objects.filter(category=user_category).exclude(
            eve__entries__userprofile__user_id=current_user_id).filter(eve__end_date__gte=datetime.date.today())\
            .exclude(eve__by=current_user_id)
        return render(request, 'website/dashboard.html', {'my_events': my_events, 'active_events': active_events,
                                                          'event_form': event_form, 'registered': registered,
                                                          'expired_events': expired_events, 'message': message,
                                                          'message_error': message_error})
    else:
        return redirect('/')


def allow(request, eid):
    entries = Entries()
    current_user_id = request.user.id
    user_profile = UserProfile.objects.get(user_id=current_user_id)
    entries.userprofile = user_profile
    entries.event = Event.objects.get(id=eid)
    entries.save()
    global message
    message = ''
    message = 'Your Entry is submitted in ' + entries.event.name
    return redirect(dashboard)


def entries(request, eventid):
    if request.user.is_authenticated():
        myevent = Event.objects.get(id=eventid)
        if myevent.by == request.user.id:
            entry = Entries.objects.filter(event_id=eventid)
            event_details = Event.objects.get(id=eventid)
            columns = EventFields.objects.get(event_id=eventid)
            return render(request, 'website/entries.html', {'entry': entry, 'event_details': event_details,
                                                            'columns': columns})
        else:
            return redirect(dashboard)
    else:
        return redirect('/')


def download(request, eventid):
    event_fields = get_object_or_404(EventFields, event_id=eventid)
    event = get_object_or_404(Event,id=eventid)
    entry = Entries.objects.filter(event_id=eventid)
    fields = []
    try:
        for field in EventFields._meta.get_all_field_names():
            if getattr(event_fields, field, False) == True:
                fields.append(field.title())
            if 'id' in fields:
                fields.remove('id')
            if 'event_id' in fields:
                fields.remove('event_id')
    except FieldDoesNotExist:
        return FieldDoesNotExist
    if 'name' in fields:
        fields.remove('name')
        fields.insert(0, 'name')
    fields = tuple(fields)
    headers = fields
    data = []
    data = tablib.Dataset(*data, headers=headers)
    for user in entry:
        val = []
        userdetail = get_object_or_404(UserProfile, id=user.userprofile_id)
        for field in fields:
            val.append(str(getattr(userdetail, field, None)))
        data.append(val)
    response = HttpResponse(data.xls, content_type='application/vnd.ms-excel;charset=utf-8')
    response['Content-Disposition'] = "attachment; filename="+event.name+".xls"

    return response


def edit_event(request, eventid):
    if request.user.is_authenticated():
        event = get_object_or_404(Event, id=eventid)
        event_form = EventForm(instance=event)
        if request.method == 'POST':
            event_form = EventForm(request.POST, instance=event)
            if event_form.is_valid():
                event = event_form.save()
                event.save()
            else:
                print("Form Error: "+event_form.errors)
    return render(request, 'website/edit-event.html', {'event_form': event_form})


def event_info(request, eventid):
    event = get_object_or_404(Event, id=eventid)
    user_by = get_object_or_404(UserProfile, user_id=event.by)

    return render(request, 'website/event-info.html', {'event': event, 'user_by': user_by.name})
